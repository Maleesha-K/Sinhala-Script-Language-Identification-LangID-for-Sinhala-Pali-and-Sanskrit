import json, subprocess, shutil, time
from pathlib import Path
import numpy as np
from .data import digest

def _transient(error):
    """A dropped transfer is worth retrying; a 404 or bad credentials is not."""
    import httpx
    if isinstance(error,(httpx.TransportError,httpx.HTTPError)): return True
    # huggingface_hub shares one httpx.Client process-wide. A failed transfer can leave it
    # closed, and every later call then raises this instead of the original network error.
    return isinstance(error,RuntimeError) and 'client has been closed' in str(error)

def _retry(call,attempts=5,delay=3):
    """Hub transfers drop mid-handshake on some networks; resume rather than lose the run."""
    from huggingface_hub.utils._http import close_session
    for attempt in range(attempts):
        try: return call()
        except Exception as error:
            if not _transient(error) or attempt==attempts-1: raise
            print(f'Hugging Face request failed ({type(error).__name__}); retry {attempt+1}/{attempts-1} in {delay}s')
            # Drop the shared client so the next attempt builds a fresh connection pool.
            close_session()
            time.sleep(delay);delay*=2

def get_base(c,name):
    spec=c['models'][name];root=Path(c['_root'])
    if spec.get('local_path'):
        p=(root/spec['local_path']).resolve()
        if not p.exists(): raise FileNotFoundError(p)
        return p,{'kind':'local','path':str(p)}
    from huggingface_hub import HfApi, hf_hub_download, snapshot_download
    lockpath=root/'models_lock.json'
    lock=json.loads(lockpath.read_text(encoding='utf8')) if lockpath.exists() else {}
    request={'repo_id':spec['repo_id'],'revision':spec.get('revision'),
             'filename':spec.get('filename')}
    if name in lock:
        if lock[name]['request']!=request:
            raise ValueError('Model source changed: use a new models_lock.json or restore the original source configuration.')
        revision=lock[name]['resolved_revision']
    else:
        revision=_retry(lambda:HfApi().model_info(spec['repo_id'],revision=spec.get('revision') or 'main').sha)
        lock[name]={'request':request,'resolved_revision':revision}
        lockpath.write_text(json.dumps(lock,indent=2),encoding='utf8')
    if name=='conlid':
        p=_retry(lambda:snapshot_download(spec['repo_id'],revision=revision,
             allow_patterns=['model.safetensors','config.json','labels.json','vocab.json','README.md','LICENSE*']))
    else:
        p=_retry(lambda:hf_hub_download(spec['repo_id'],spec['filename'],revision=revision))
    return Path(p),lock[name]

class NativeFastText:
    def __init__(self,path,root):
        from scripts.build_native import build
        self.path=Path(path);self.root=Path(root)
        self.exe=build(Path(__file__).resolve().parents[1])
        content=subprocess.check_output([str(self.exe),'inspect',str(self.path)],text=True)
        self.metadata={};self.labels=[]
        for row in content.splitlines():
            key,value=row.split('\t',1)
            if key=='label': self.labels.append(value.removeprefix('__label__'))
            else: self.metadata[key]=value
        if self.metadata['loss']!='softmax':
            raise ValueError(f'Expected released softmax checkpoint, got {self.metadata}. The package will not silently replace its output head.')

    def initialize(self,labels,out):
        out=Path(out);out.mkdir(parents=True,exist_ok=True)
        labelpath=out/'labels_to_add.txt'
        labelpath.write_text(''.join('__label__'+l+'\n' for l in labels),encoding='utf8')
        dest=out/'model.bin'
        subprocess.run([str(self.exe),'train',str(self.path),str(labelpath),str(labelpath),str(dest),'0.05','0','42'],check=True)
        child=NativeFastText(dest,self.root)
        if child.labels[:len(self.labels)]!=self.labels: raise AssertionError('Old label order changed')
        return child

    def train(self,df,out,lr,examples,seed,batch_size=1):
        from .data import write_fasttext
        out=Path(out);out.mkdir(parents=True,exist_ok=True)
        datafile=out/'training.fasttext';labelsfile=out/'training_labels.txt'
        write_fasttext(df,datafile)
        labelsfile.write_text(''.join('__label__'+l+'\n' for l in sorted(set(df.label))),encoding='utf8')
        missing=set(df.label)-set(self.labels)
        if missing: raise ValueError(f'Initialize missing labels before training: {missing}')
        subprocess.run([str(self.exe),'train',str(self.path),str(datafile),str(labelsfile),str(out/'model.bin'),str(lr),str(examples),str(seed)],check=True)
        datafile.unlink() # keep the original CSV and its hash; avoid duplicate private text files
        return NativeFastText(out/'model.bin',self.root)

    def predict(self,texts,workdir,batch_size=32):
        workdir=Path(workdir);workdir.mkdir(parents=True,exist_ok=True)
        inputfile=workdir/'_prediction_input.txt';outputfile=workdir/'_prediction_output.tsv'
        inputfile.write_text(''.join(t+'\n' for t in texts),encoding='utf8')
        try:
            subprocess.run([str(self.exe),'predict',str(self.path),str(inputfile),str(outputfile)],check=True)
            rows=[line.split('\t') for line in outputfile.read_text(encoding='utf8').splitlines()]
            return [r[0] for r in rows],[float(r[1]) for r in rows]
        finally:
            inputfile.unlink(missing_ok=True);outputfile.unlink(missing_ok=True)

    def checkpoint_hash(self): return digest(self.path)

def conlid_class():
    """Independent implementation of the released ConLID inference architecture.

    Same signed-byte FNV hash, character ngrams, vocab offsets and pooled linear
    head. EmbeddingBag avoids padding/memory blowups and keeps encoder gradients.
    No contrastive loss is added: this experiment is supervised CE adaptation.
    """
    import re, torch
    from torch import nn
    class ConLIDWeights(nn.Module):
        def __init__(self,config,vocab,labels):
            super().__init__()
            if config['aggr'] not in ('mean','sum'):
                raise ValueError('This release supports mean/sum aggregation; inspect a changed upstream model before using it.')
            self.config=dict(config);self.vocab=vocab
            self.labels=[s for s,i in sorted(labels.items(),key=lambda x:x[1])]
            if sorted(labels.values())!=list(range(len(labels))): raise ValueError('Noncontiguous label IDs')
            self.embedding=nn.EmbeddingBag(config['vocab_size'],config['embedding_size'],mode=config['aggr'],sparse=True)
            self.fc=nn.Linear(config['embedding_size'],config['num_classes'])

        @staticmethod
        def hash_ngram(s):
            h=2166136261
            for b in s.encode('utf8'):
                h=((h ^ (b if b<128 else b-256))*16777619)&0xffffffff
            return h

        def encode(self,text):
            ids=[];cfg=self.config
            for word in re.split(r'[\n\t\v\r\f\x00 ]+',text):
                word=word.strip()
                if not word: continue
                if word in self.vocab: ids.append(self.vocab[word])
                if cfg['bucket']>0 and cfg['maxn']>0:
                    padded='<'+word+'>'
                    for n in range(cfg['minn'],cfg['maxn']+1):
                        for start in range(len(padded)-n+1):
                            ids.append(len(self.vocab)+self.hash_ngram(padded[start:start+n])%cfg['bucket'])
            ids=[i for i in ids if i not in (cfg.get('pad_id',0),cfg.get('unk_id',1))]
            if not ids: raise ValueError('Text yields no ConLID features; inspect the input instead of silently fabricating predictions.')
            if min(ids)<0 or max(ids)>=self.embedding.num_embeddings: raise ValueError('Vocabulary/bucket mismatch in ConLID checkpoint')
            return ids

        def tensors(self,features,device):
            lengths=[len(x) for x in features]
            offsets=np.concatenate(([0],np.cumsum(lengths)[:-1]))
            return (torch.tensor([i for row in features for i in row],dtype=torch.long,device=device),
                    torch.tensor(offsets,dtype=torch.long,device=device))

        def forward(self,ids,offsets): return self.fc(self.embedding(ids,offsets))

        def add_labels(self,requested):
            new=[s for s in requested if s not in self.labels]
            if not new: return
            old=self.fc;head=nn.Linear(old.in_features,old.out_features+len(new),device=old.weight.device)
            with torch.no_grad():
                head.weight.zero_();head.bias.zero_()
                head.weight[:old.out_features].copy_(old.weight)
                head.bias[:old.out_features].copy_(old.bias)
            self.fc=head;self.labels+=new;self.config['num_classes']=len(self.labels)
    return ConLIDWeights

class ConLIDBackend:
    def __init__(self,path,device='auto'):
        import torch
        from safetensors.torch import load_file
        self.path=Path(path)
        if device=='auto': device='cuda' if torch.cuda.is_available() else 'cpu'
        self.device=device
        config=json.loads((self.path/'config.json').read_text(encoding='utf8'))
        vocab=json.loads((self.path/'vocab.json').read_text(encoding='utf8'))
        labels=json.loads((self.path/'labels.json').read_text(encoding='utf8'))
        self.model=conlid_class()(config,vocab,labels)
        self.model.load_state_dict(load_file(str(self.path/'model.safetensors')),strict=True)
        self.model.to(device);self.model.eval()
        self.labels=self.model.labels
        self.metadata={'labels':len(self.labels),'config':config,'device':device,'adaptation_loss':'cross_entropy'}

    def save(self,path):
        from safetensors.torch import save_file
        path=Path(path);path.mkdir(parents=True,exist_ok=True)
        save_file({k:v.detach().cpu().contiguous() for k,v in self.model.state_dict().items()},str(path/'model.safetensors'))
        for filename,obj in [('config.json',self.model.config),('vocab.json',self.model.vocab),
                              ('labels.json',{l:i for i,l in enumerate(self.labels)})]:
            (path/filename).write_text(json.dumps(obj,ensure_ascii=False),encoding='utf8')
        self.path=path

    def initialize(self,labels,out):
        self.model.add_labels(labels);self.labels=self.model.labels;self.save(out)
        return self

    def train(self,df,out,lr,examples,seed,batch_size=32):
        import torch,time
        from tqdm.auto import tqdm
        from torch.nn import functional as F
        torch.manual_seed(seed);rng=np.random.default_rng(seed)
        self.model.train();lookup={s:i for i,s in enumerate(self.labels)}
        # Compact arrays avoid millions of Python integer objects on real corpora.
        features=[np.asarray(self.model.encode(t),dtype=np.int32)
                  for t in tqdm(df.text,desc='Tokenizing ConLID')]
        targets=np.array([lookup[s] for s in df.label])
        optimizer=torch.optim.SGD(self.model.parameters(),lr=lr) # sparse gradients; no dense Adam state
        order=rng.permutation(len(df));pos=0;seen=0;history=[];start=time.time()
        with tqdm(total=examples,desc='Training ConLID (examples)') as bar:
            while seen<examples:
                take=min(batch_size,examples-seen,len(order)-pos)
                chosen=order[pos:pos+take];pos+=take
                ids,offsets=self.model.tensors([features[i] for i in chosen],self.device)
                y=torch.tensor(targets[chosen],dtype=torch.long,device=self.device)
                optimizer.zero_grad(set_to_none=True)
                loss=F.cross_entropy(self.model(ids,offsets),y)
                if not torch.isfinite(loss): raise FloatingPointError('Nonfinite ConLID training loss')
                loss.backward()
                if self.model.embedding.weight.grad is None: raise AssertionError('Encoder gradient was detached')
                rate=lr*(1-seen/examples)
                for group in optimizer.param_groups: group['lr']=rate
                optimizer.step();seen+=take;bar.update(take)
                if len(history)==0 or seen-history[-1]['examples_seen']>=1000 or seen==examples:
                    history.append({'examples_seen':seen,'loss':float(loss.detach()),'lr':rate,'seconds':time.time()-start})
                if pos==len(order): order=rng.permutation(len(df));pos=0
        self.model.eval();self.save(out)
        import pandas as pd
        pd.DataFrame(history).to_csv(Path(out)/'training_history.csv',index=False)
        return self

    def predict(self,texts,workdir,batch_size=32):
        import torch
        self.model.eval();raw=[];confidence=[];texts=list(texts)
        with torch.inference_mode():
            for start in range(0,len(texts),batch_size):
                features=[self.model.encode(t) for t in texts[start:start+batch_size]]
                ids,offsets=self.model.tensors(features,self.device)
                logits=self.model(ids,offsets)
                if not torch.isfinite(logits).all(): raise FloatingPointError('Nonfinite ConLID logits')
                p,i=logits.softmax(-1).max(-1)
                raw.extend(self.labels[j] for j in i.cpu().tolist());confidence.extend(p.cpu().tolist())
        return raw,confidence

    def checkpoint_hash(self):
        return {name:digest(self.path/name) for name in ['model.safetensors','config.json','labels.json','vocab.json']}
