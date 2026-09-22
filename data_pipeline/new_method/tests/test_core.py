import json, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lidlab.data import TARGET,REPLAY,LANGUAGES,prepare,load_config,canonical_label
from lidlab.metrics import score_predictions,evaluate,make_tables
from lidlab.backends import NativeFastText,ConLIDBackend
from scripts.build_native import build

def test_metrics_count_out_of_set_predictions():
    scores=score_predictions(['sin_Sinh','sin_Sinh','pli_Sinh'],['sin_Sinh','fra_Latn','sin_Sinh']).set_index('language')
    assert scores.loc['sin_Sinh','f1']==pytest.approx(0.5)
    assert scores.loc['pli_Sinh','f1']==0
    assert np.isnan(scores.loc['san_Sinh','f1'])
    assert canonical_label('san_Deva')!='san_Sinh'

def test_native_continuation_and_saved_format(tmp_path):
    ft=pytest.importorskip('fasttext')
    exe=build(ROOT)
    train=tmp_path/'base.txt';base=tmp_path/'base.bin'
    train.write_text(('__label__eng_Latn hello world English text\n__label__fra_Latn bonjour monde texte français\n')*12)
    subprocess.run([str(exe),'toy',str(train),str(base)],check=True)
    backend=NativeFastText(base,ROOT)
    initialized=backend.initialize(TARGET,tmp_path/'init')
    old=ft.load_model(str(base));init=ft.load_model(str(initialized.path))
    np.testing.assert_array_equal(old.get_input_matrix(),init.get_input_matrix())
    np.testing.assert_array_equal(old.get_output_matrix(),init.get_output_matrix()[:len(old.labels)])
    assert init.labels[:len(old.labels)]==old.labels
    # Prediction behavior matches the official loader, including word ngrams.
    probes=['hello world English text','bonjour monde texte français','සිංහල පෙළ']
    labels,probs=backend.predict(probes,tmp_path/'pred')
    for text,label,p in zip(probes,labels,probs):
        ref=old.f.predict(text+'\n',1,0.0,'strict')
        assert label==ref[0][1]
        assert p==pytest.approx(ref[0][0],abs=1e-6)
    df=pd.DataFrame({'text':['සිංහල භාෂාව','ධම්ම බුද්ධ පාලි','සංස්කෘත භාෂා'],'label':TARGET})
    updated=initialized.train(df,tmp_path/'trained',0.2,30,42)
    final=ft.load_model(str(updated.path))
    assert final.labels==init.labels
    assert not np.array_equal(final.get_input_matrix(),init.get_input_matrix())
    assert not np.array_equal(final.get_output_matrix(),init.get_output_matrix())

def make_conlid_checkpoint(path,labels=None):
    import torch
    from safetensors.torch import save_file
    from lidlab.backends import conlid_class
    labels=labels or ['eng_Latn','fra_Latn']
    cfg={'vocab_size':105,'embedding_size':8,'num_classes':len(labels),'bucket':100,
         'min_count':1,'minn':2,'maxn':4,'aggr':'mean'}
    vocab={'<pad>':0,'<unk>':1,'hello':2,'bonjour':3,'world':4}
    mapping={s:i for i,s in enumerate(labels)}
    model=conlid_class()(cfg,vocab,mapping)
    torch.manual_seed(13)
    with torch.no_grad():
        model.embedding.weight.normal_(0,.1);model.fc.weight.normal_(0,.1);model.fc.bias.zero_()
    path.mkdir(parents=True)
    save_file(model.state_dict(),str(path/'model.safetensors'))
    for name,obj in [('config.json',cfg),('vocab.json',vocab),('labels.json',mapping)]:
        (path/name).write_text(json.dumps(obj))
    return model

def test_conlid_preserves_weights_and_trains_encoder(tmp_path):
    torch=pytest.importorskip('torch')
    ref=make_conlid_checkpoint(tmp_path/'base')
    b=ConLIDBackend(tmp_path/'base','cpu')
    oldembed=b.model.embedding.weight.detach().clone()
    oldfc=b.model.fc.weight.detach().clone()
    b.initialize(TARGET,tmp_path/'init')
    torch.testing.assert_close(b.model.embedding.weight,oldembed,rtol=0,atol=0)
    torch.testing.assert_close(b.model.fc.weight[:2],oldfc,rtol=0,atol=0)
    # Pooling agrees with explicit per-sentence mean over the loaded embedding rows.
    features=[b.model.encode(t) for t in ['hello world','සිංහල භාෂාව']]
    ids,offsets=b.model.tensors(features,'cpu')
    dense=torch.stack([oldembed[x].mean(0) for x in features])
    torch.testing.assert_close(b.model.embedding(ids,offsets),dense)
    df=pd.DataFrame({'text':['සිංහල භාෂාව','ධම්ම බුද්ධ පාලි','සංස්කෘත භාෂා'],'label':TARGET})
    b.train(df,tmp_path/'trained',0.2,20,42,batch_size=2)
    assert not torch.equal(oldembed,b.model.embedding.weight)
    assert b.labels[:2]==['eng_Latn','fra_Latn']
    loaded=ConLIDBackend(tmp_path/'trained','cpu')
    assert loaded.predict(df.text,tmp_path)[0]==b.predict(df.text,tmp_path)[0]

def make_data(root):
    c=load_config(ROOT/'config.json');c['_root']=str(root)
    (root/'data').mkdir()
    groups=dict(zip(LANGUAGES,['Sinhala-Sinh','Pali-Sinh','Sanskrit-Sinh','Sanskrit-Deva',
        'English-Latn','Tamil-Taml','Hindi-Deva','Bengali-Beng','Arabic-Arab','French-Latn','German-Latn']))
    for key,labels in [('train',TARGET),('validation',TARGET),('target_test',TARGET)]:
        rows=[]
        for i,label in enumerate(labels):
            stem='සිංහල පාලි සංස්කෘත' if label.endswith('_Sinh') else 'संस्कृत भाषा' if label=='san_Deva' else 'distinct language sentence'
            row={'text':f'{stem} {key} {label} number{i}','label':label,'group_id':f'{key}:{label}'}
            rows.append(row)
        frame=pd.DataFrame(rows)
        frame.to_csv(root/c['data'][key],index=False)
    for key in ['mixed_train','mixed_validation']:
        rows=[]
        for i,label in enumerate(LANGUAGES):
            stem='සිංහල පාලි සංස්කෘත' if label.endswith('_Sinh') else 'संस्कृत भाषा' if label=='san_Deva' else 'distinct language sentence'
            rows.append({'text':f'{stem} {key} {label} number{i}','label':label.split('_')[0],
                         'group':groups[label],'group_id':f'{key}:{label}'})
        pd.DataFrame(rows).to_json(root/c['data'][key],orient='records',lines=True,force_ascii=False)
    for benchmark,path in c['data']['benchmarks'].items():
        rows=[]
        for i,label in enumerate(LANGUAGES):
            stem='සිංහල පාලි සංස්කෘත' if label.endswith('_Sinh') else 'संस्कृत भाषा' if label=='san_Deva' else 'distinct benchmark sentence'
            rows.append({'text':f'{stem} {benchmark} {label} number{i}',
                         'label':label.split('_')[0],'source':benchmark})
        destination=root/path;destination.parent.mkdir(parents=True,exist_ok=True)
        pd.DataFrame(rows).to_json(destination,orient='records',lines=True,force_ascii=False)
    return c

def test_leakage_checks(tmp_path):
    c=make_data(tmp_path);c['require_document_ids']=True;data=prepare(c)
    assert len(data['mixed_train'])==11
    valpath=tmp_path/c['data']['validation'];val=pd.read_csv(valpath)
    val.loc[0,'group_id']=data['train'].doc_id.iloc[0];val.to_csv(valpath,index=False)
    with pytest.raises(ValueError,match='Document leakage'): prepare(c)

def test_benchmark_duplicates_are_safe(tmp_path):
    c=make_data(tmp_path)
    path=tmp_path/c['data']['benchmarks']['commonlid']
    rows=pd.read_json(path,lines=True,dtype=False)
    rows=pd.concat([rows,rows.iloc[[0]]],ignore_index=True)
    rows.to_json(path,orient='records',lines=True,force_ascii=False)
    data=prepare(c)
    assert len(data['benchmarks']['commonlid'])==len(LANGUAGES)
    assert data['audit']['files']['benchmark_commonlid']['same_label_duplicates_removed']==1
    rows.loc[len(rows)-1,'label']='pli'
    rows.loc[len(rows)]={'text':'සිංහල වෙනත් පාඨය','label':'sin','source':'commonlid'}
    rows.to_json(path,orient='records',lines=True,force_ascii=False)
    data=prepare(c)
    audit=data['audit']['files']['benchmark_commonlid']
    assert audit['conflicting_text_types_removed']==1
    assert audit['conflicting_rows_removed']==2

def test_full_pipeline_small_conlid(tmp_path):
    from lidlab.experiment import run_experiment
    c=make_data(tmp_path)
    labels=['sin_Sinh']+REPLAY+['spa_Latn']
    make_conlid_checkpoint(tmp_path/'base',labels)
    c['models']['conlid']['local_path']='base';c['device']='cpu';c['target_passes']=4
    result=run_experiment(c,'conlid')
    assert set(result)=={'zero_shot','target_only','replay'}
    assert set(result['zero_shot'])==set(c['data']['benchmarks'])
    root=tmp_path/c['output_dir']/'conlid'
    target=json.loads((root/'target_only/complete.json').read_text())
    replay=json.loads((root/'replay/complete.json').read_text())
    assert target['training']['initialization']==replay['training']['initialization']
    assert target['n_final_labels']==len(labels)+2
    # A repeated unchanged run reuses completed phases.
    run_experiment(c,'conlid')
    # Sequential recovery must actually load the target-only result.
    c['replay_start']='target_only';c['output_dir']='results/sequential'
    run_experiment(c,'conlid')
    recovery=json.loads((tmp_path/c['output_dir']/'conlid/replay/complete.json').read_text())
    assert recovery['training']['initialization'].endswith('target_only')

def test_all_models_tables_and_zero_import(tmp_path):
    from lidlab.experiment import run_experiment
    from lidlab.metrics import import_zero_predictions
    c=make_data(tmp_path);c['target_passes']=4;c['device']='cpu'
    labels=['sin_Sinh']+REPLAY+['spa_Latn']
    make_conlid_checkpoint(tmp_path/'conlid_base',labels)
    c['models']['conlid']['local_path']='conlid_base'
    training=tmp_path/'base.txt'
    training.write_text(''.join(f'__label__{label} base distinct tokens for {label}\n' for _ in range(5) for label in labels))
    subprocess.run([str(build(ROOT)),'toy',str(training),str(tmp_path/'base.bin')],check=True)
    c['models']['nllb']['local_path']='base.bin'
    c['models']['glotlid']['local_path']='base.bin'
    for name in ['nllb','glotlid','conlid']: run_experiment(c,name)
    tables=make_tables(c)
    assert all(x.shape==(9,14) for x in tables.values())
    root=tmp_path/c['output_dir']
    prepared=prepare(c)
    benchmark='flores_plus';frame=prepared['benchmarks'][benchmark]
    imported=import_zero_predictions(root/f'nllb/zero_shot/benchmarks/{benchmark}/predictions.csv',frame,tmp_path/'imported')[0]
    original=pd.read_csv(root/f'nllb/zero_shot/benchmarks/{benchmark}/per_language.csv')
    np.testing.assert_allclose(imported.f1,original.f1)
    pred=pd.read_csv(root/f'nllb/zero_shot/benchmarks/{benchmark}/predictions.csv');pred.loc[0,'text_sha256']='wrong'
    pred.to_csv(tmp_path/'bad_predictions.csv',index=False)
    with pytest.raises(ValueError,match='different texts'):
        import_zero_predictions(tmp_path/'bad_predictions.csv',frame,tmp_path/'badimport')
