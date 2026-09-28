"""One-vs-rest metrics: unrestricted predictions; no filtering to 11 outputs."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .data import canonical_label, TARGET, REPLAY, LANGUAGES, NAMES

def score_predictions(gold,pred):
    if len(gold)!=len(pred): raise ValueError('Prediction count mismatch')
    y=np.asarray(gold,dtype=str);p=np.asarray(pred,dtype=str)
    rows=[]
    for label in LANGUAGES:
        tp=int(((y==label)&(p==label)).sum())
        fp=int(((y!=label)&(p==label)).sum())
        fn=int(((y==label)&(p!=label)).sum())
        support=int((y==label).sum())
        rows.append({'language':label,'precision':tp/(tp+fp) if tp+fp else 0.,
          'recall':tp/(tp+fn) if tp+fn else 0.,'f1':2*tp/(2*tp+fp+fn) if support else np.nan,
          'support':support,'tp':tp,'fp':fp,'fn':fn})
    return pd.DataFrame(rows)

def evaluate(df,raw,probs,out,aliases=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    pred=[canonical_label(s,aliases) for s in raw]
    scores=score_predictions(df.label,pred)
    saved=df[['sample_id','text_sha256','label']].copy()
    saved['prediction_raw']=raw;saved['prediction']=pred;saved['confidence']=probs
    saved.to_csv(out/'predictions.csv',index=False)
    scores.to_csv(out/'per_language.csv',index=False)
    summary={'accuracy':float(np.mean(np.asarray(df.label)==np.asarray(pred))),
       'macro_f1_11':float(scores.f1.mean()),
       'macro_f1_target3':float(scores.loc[scores.language.isin(TARGET),'f1'].mean()),
       'macro_f1_replay8':float(scores.loc[scores.language.isin(REPLAY),'f1'].mean()),
       'categories_scored':int(scores.f1.notna().sum()),
       'outside_11_predictions':sum(s not in LANGUAGES for s in pred),
       'n_test':len(df),'scope':'unrestricted full-model top-1; no threshold; strict script tags; arb_Arab means Modern Standard Arabic only (ara macrolanguage NOT mapped in)'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    pd.crosstab(pd.Series(df.label.to_list(),name='gold'),pd.Series(pred,name='predicted')).to_csv(out/'confusion.csv')
    return scores,summary

def import_zero_predictions(path,df,out,aliases=None):
    """Import per-sample results only after IDs and normalized text hashes match."""
    old=pd.read_csv(path,dtype={'sample_id':str,'text_sha256':str})
    required={'sample_id','text_sha256','prediction_raw'}
    if not required<=set(old): raise ValueError(f'Existing zero-shot predictions need columns {required}. Aggregate F1 alone cannot establish an identical protocol.')
    if old.sample_id.duplicated().any() or set(old.sample_id)!=set(df.sample_id):
        raise ValueError('Existing zero-shot sample IDs do not exactly match this evaluation set')
    old=old.set_index('sample_id').loc[df.sample_id].reset_index()
    if old.text_sha256.tolist()!=df.text_sha256.tolist(): raise ValueError('Existing predictions use different texts/order/normalization')
    return evaluate(df,old.prediction_raw.tolist(),old.get('confidence',pd.Series([np.nan]*len(old))).tolist(),out,aliases)

def make_tables(c):
    root=Path(c['_root'])/c['output_dir'];dest=root/'tables';dest.mkdir(exist_ok=True)
    phases=['zero_shot','target_only','replay']
    models=['nllb','glotlid','conlid'];tables={}
    all_test_keys=set(); model_signatures={}
    benchmarks=list(c['data']['benchmarks'])
    for number,phase in enumerate(phases,1):
        values={}
        eval_keys=[]
        for model in models:
            d=root/model/phase
            if not (d/'complete.json').exists(): raise FileNotFoundError(f'Finish {model}/{phase} before exporting tables')
            manifest=json.loads((d/'complete.json').read_text(encoding='utf8'))
            key=json.dumps(manifest['benchmark_sha256'],sort_keys=True)
            eval_keys.append(key);all_test_keys.add(key)
            if model in model_signatures and model_signatures[model]!=manifest['signature']:
                raise ValueError(f'{model}: phases have different experiment protocols')
            model_signatures[model]=manifest['signature']
            for benchmark in benchmarks:
                values[f'{model} — {benchmark}']=pd.read_csv(d/'benchmarks'/benchmark/'per_language.csv').set_index('language').loc[LANGUAGES,'f1']
        if len(set(eval_keys))!=1: raise ValueError('Models were evaluated on different test files')
        table=pd.DataFrame(values).T
        table.columns=NAMES
        table['Macro F1 (target 3)']=table.iloc[:,:3].mean(axis=1)
        table['Macro F1 (replay 8)']=table.iloc[:,3:11].mean(axis=1)
        table['Macro F1 (all 11)']=table.iloc[:,:11].mean(axis=1)
        name=f'table_{number}_{phase}'
        table.to_csv(dest/(name+'.csv'),float_format='%.6f')
        table.to_latex(dest/(name+'.tex'),float_format=lambda x:f'{x:.4f}',escape=True)
        tables[phase]=table
    if len(all_test_keys)!=1: raise ValueError('The three tables do not use the same test file')
    # Positive drop means forgetting; negative values mean improvement.
    drops=tables['zero_shot']-tables['target_only']
    recovery=tables['replay']-tables['target_only']
    residual=tables['zero_shot']-tables['replay']
    drops.to_csv(dest/'forgetting_zero_minus_target.csv')
    recovery.to_csv(dest/'recovery_replay_minus_target.csv')
    residual.to_csv(dest/'residual_zero_minus_replay.csv')
    return tables
