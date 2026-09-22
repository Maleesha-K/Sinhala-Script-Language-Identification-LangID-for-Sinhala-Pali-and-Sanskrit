import gc, hashlib, json, platform, subprocess, sys, time
from pathlib import Path
import pandas as pd
from .data import prepare, TARGET, REPLAY
from .backends import NativeFastText, ConLIDBackend, get_base
from .metrics import evaluate, import_zero_predictions

def _load(c,name,path):
    return ConLIDBackend(path,c['device']) if name=='conlid' else NativeFastText(path,c['_root'])

def _release(model):
    del model;gc.collect()
    if 'torch' in sys.modules:
        import torch
        if torch.cuda.is_available(): torch.cuda.empty_cache()

def run_experiment(c,name,phases=('zero_shot','target_only','replay')):
    """One original checkpoint, one expanded initialization, two training arms.

    Default: base -> target_only; base -> mixed replay.
    replay_start='target_only' explicitly selects the sequential recovery study.
    Every arm sees target_passes * len(train) examples (matched compute).
    """
    if name not in c['models']: raise ValueError(name)
    if c['replay_start'] not in ('base','target_only'): raise ValueError('replay_start must be base or target_only')
    data=prepare(c)
    basepath,source=get_base(c,name)
    root=Path(c['_root'])/c['output_dir']/name;root.mkdir(parents=True,exist_ok=True)
    spec=c['models'][name]
    examples=int(c['target_passes']*len(data['train']))
    if examples<1: raise ValueError('Training budget must be positive')
    if examples<len(data['mixed_train']):
        raise ValueError('Increase target_passes: the matched budget must cover every row of the mixed dataset at least once.')
    backend=_load(c,name,basepath)
    basehash=backend.checkpoint_hash();original_labels=list(backend.labels)
    if not set(REPLAY)<=set(original_labels):
        raise ValueError(f'Replay languages missing from this base model: {set(REPLAY)-set(original_labels)}. Check checkpoint and label names before calling this retention.')
    config={k:v for k,v in c.items() if k not in ('_root','output_dir')}
    protocol={'config':config,'data_files':data['audit']['files'],'base_checkpoint_sha256':basehash,
        'source':source,'seed':c['seed'],'examples_per_arm':examples,
        'full_output_space':True,'original_labels':original_labels,
        'base_metadata':backend.metadata,'python':sys.version,'platform':platform.platform()}
    signature=hashlib.sha256(json.dumps(protocol,sort_keys=True).encode()).hexdigest()
    old=root/'protocol.json'
    if old.exists() and json.loads(old.read_text(encoding='utf8'))['signature']!=signature:
        raise ValueError(f'Configuration/data/checkpoint changed. Use a new output_dir instead of mixing results in {root}.')
    protocol['signature']=signature;old.write_text(json.dumps(protocol,indent=2),encoding='utf8')
    freeze=subprocess.run([sys.executable,'-m','pip','freeze'],capture_output=True,text=True,check=True)
    (root/'environment.txt').write_text(freeze.stdout,encoding='utf8')
    testhashes={name:data['audit']['files']['benchmark_'+name]['sha256'] for name in data['benchmarks']}

    def done(phase):
        path=root/phase/'complete.json'
        if not path.exists(): return False
        if json.loads(path.read_text(encoding='utf8'))['signature']!=signature: raise ValueError('Stale phase results')
        return True

    def finish(phase,model,training=None):
        folder=root/phase;folder.mkdir(parents=True,exist_ok=True)
        labels=list(model.labels)
        if labels[:len(original_labels)]!=original_labels: raise AssertionError('Original labels were removed/reordered')
        existing=spec.get('existing_zero_predictions') if phase=='zero_shot' else None
        benchmark_summaries={}
        for benchmark,frame in data['benchmarks'].items():
            destination=folder/'benchmarks'/benchmark
            existing_path=existing.get(benchmark) if isinstance(existing,dict) else None
            if existing_path:
                evaluate_result=import_zero_predictions(Path(c['_root'])/existing_path,frame,destination,c.get('label_aliases'))
            else:
                pred,prob=model.predict(frame.text,destination,c['conlid_batch_size'])
                evaluate_result=evaluate(frame,pred,prob,destination,c.get('label_aliases'))
            benchmark_summaries[benchmark]=evaluate_result[1]
        # Validation and the supplemental three-label test are kept separate.
        validation=data['validation'] if phase=='target_only' else data['mixed_validation']
        pred,prob=model.predict(validation.text,folder/'validation',c['conlid_batch_size'])
        evaluate(validation,pred,prob,folder/'validation',c.get('label_aliases'))
        pred,prob=model.predict(data['target_test'].text,folder/'target_test',c['conlid_batch_size'])
        evaluate(data['target_test'],pred,prob,folder/'target_test',c.get('label_aliases'))
        completed={'signature':signature,'benchmark_sha256':testhashes,'benchmark_summaries':benchmark_summaries,
          'base_checkpoint_sha256':basehash,
          'checkpoint_sha256':model.checkpoint_hash(),'training':training,'n_original_labels':len(original_labels),
          'n_final_labels':len(labels),'phase':phase,'replay_start':c['replay_start']}
        (folder/'complete.json').write_text(json.dumps(completed,indent=2),encoding='utf8')
        print(name,phase,{k:round(v['macro_f1_11'],4) for k,v in benchmark_summaries.items()})

    if 'zero_shot' in phases and not done('zero_shot'):
        finish('zero_shot',backend)
    # No random replacement head; only add missing target rows, identically for both arms.
    init=root/'initialized'
    weightfile='model.safetensors' if name=='conlid' else 'model.bin'
    initpath=init if name=='conlid' else init/weightfile
    if not (init/'complete.json').exists():
        backend=backend.initialize(TARGET,init)
        finish('initialized',backend)
    _release(backend);del backend;gc.collect()
    for phase in ('target_only','replay'):
        if phase not in phases or done(phase): continue
        if phase=='replay' and c['replay_start']=='target_only':
            if not done('target_only'): raise ValueError('Sequential recovery requires target_only first.')
            startpath=root/'target_only' if name=='conlid' else root/'target_only'/weightfile
        else: startpath=initpath
        backend=_load(c,name,startpath)
        df=data['train'] if phase=='target_only' else data['mixed_train']
        training={'initialization':str(startpath),'examples_seen':examples,'unique_training_rows':len(df),
          'nominal_passes_over_arm_data':examples/len(df),'learning_rate':spec['lr'],'seed':c['seed'],
          'class_counts':df.label.value_counts().to_dict(),
          'replay_fraction_in_pool':0.0 if phase=='target_only' else float(df.label.isin(REPLAY).mean()),
          'loss':'cross_entropy over full output space','selection':'fixed budget; no test-based selection'}
        started=time.time()
        backend=backend.train(df,root/phase,spec['lr'],examples,c['seed'],c['conlid_batch_size'])
        training['seconds']=time.time()-started
        finish(phase,backend,training)
        _release(backend);del backend;gc.collect()
    return {phase:{benchmark:pd.read_csv(root/phase/'benchmarks'/benchmark/'per_language.csv')
                   for benchmark in data['benchmarks']} for phase in phases if done(phase)}
