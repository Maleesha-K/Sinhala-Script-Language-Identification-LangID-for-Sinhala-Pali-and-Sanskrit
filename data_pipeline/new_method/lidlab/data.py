import hashlib, json, re, unicodedata
from pathlib import Path
import pandas as pd

TARGET=['sin_Sinh','pli_Sinh','san_Sinh']
REPLAY=['san_Deva','eng_Latn','tam_Taml','hin_Deva','ben_Beng','arb_Arab','fra_Latn','deu_Latn']
LANGUAGES=TARGET+REPLAY
NAMES=['Sinhala (Sinhala)','Pali (Sinhala)','Sanskrit (Sinhala)','Sanskrit (Devanagari)',
       'English','Tamil','Hindi','Bengali','Modern Standard Arabic','French','German']
ALIASES={'si':'sin_Sinh','sin':'sin_Sinh','sinhala':'sin_Sinh',
         'pi':'pli_Sinh','pli':'pli_Sinh','pali':'pli_Sinh',
         'sa':'san_Sinh','san':'san_Sinh','sanskrit':'san_Sinh',
         'en':'eng_Latn','eng':'eng_Latn','ta':'tam_Taml','tam':'tam_Taml',
         'hi':'hin_Deva','hin':'hin_Deva','bn':'ben_Beng','ben':'ben_Beng',
         'ar':'arb_Arab','arb':'arb_Arab','fr':'fra_Latn','fra':'fra_Latn',
         'de':'deu_Latn','deu':'deu_Latn','arb_Arab':'arb_Arab',
         'Sinhala-Sinh':'sin_Sinh','Pali-Sinh':'pli_Sinh',
         'Sanskrit-Sinh':'san_Sinh','Sanskrit-Deva':'san_Deva',
         'English-Latn':'eng_Latn','Tamil-Taml':'tam_Taml',
         'Hindi-Deva':'hin_Deva','Bengali-Beng':'ben_Beng',
         'Arabic-Arab':'arb_Arab','French-Latn':'fra_Latn','German-Latn':'deu_Latn'}

def canonical_label(value,aliases=None):
    value=str(value).removeprefix('__label__').strip()
    return {**ALIASES,**(aliases or {})}.get(value,value)

def clean_text(value,normalization='NFC'):
    value=str(value)
    if normalization: value=unicodedata.normalize(normalization,value)
    return re.sub(r'\s+',' ',value.replace('\x00',' ').replace('\ufeff',' ').replace('\u200b',' ')).strip()

def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def text_hash(text): return hashlib.sha256(text.encode('utf8')).hexdigest()

def load_config(path='config.json'):
    path=Path(path).resolve()
    c=json.loads(path.read_text(encoding='utf8'))
    c['_root']=str(path.parent)
    return c

def resolve(c,path): return Path(c['_root'])/path

def read_data(c,key):
    path=resolve(c,c['data'][key])
    if not path.exists(): raise FileNotFoundError(f'Missing {path}. See data/README.md and notebook 00.')
    if path.suffix.lower() in ('.jsonl','.ndjson'):
        raw=pd.read_json(path,lines=True,dtype=False).fillna('')
    else:
        raw=pd.read_csv(path,keep_default_na=False,dtype=str,encoding='utf-8-sig')
    raw=raw.astype(str)
    cols=c['columns']
    missing={cols['text'],cols['label']}-set(raw.columns)
    if missing: raise ValueError(f'{path.name}: missing columns {missing}; edit config.json columns.')
    # The supplied mixed JSONL distinguishes san_Sinh from san_Deva in `group`.
    # Prefer that explicit language-script group whenever it is present.
    if cols.get('group') in raw.columns:
        explicit=raw[cols['group']].str.strip()
        label_values=explicit.where(explicit!='',raw[cols['label']])
    else:
        label_values=raw[cols['label']]
    out=pd.DataFrame({'text':raw[cols['text']].map(lambda s:clean_text(s,c['normalization'])),
                      'label':label_values.map(lambda s:canonical_label(s,c.get('label_aliases')))})
    group=cols.get('doc_id')
    if group and group in raw:
        out['doc_id']=raw[group]
        if (out.doc_id=='').any() and c['require_document_ids']:
            raise ValueError(f'{path.name}: empty document IDs')
    elif c['require_document_ids']:
        raise ValueError(f'{path.name}: preserve original document IDs in {group!r}; do not invent one per training sentence. Set require_document_ids=false only if original IDs cannot be recovered (weaker leakage check).')
    if out.empty or (out.text=='').any() or (out.label=='').any():
        raise ValueError(f'{path.name}: empty text/label/data')
    if out.text.str.contains('__label__',regex=False).any():
        raise ValueError(f'{path.name}: text contains fastText label marker; remove label leakage from text.')
    out['text_sha256']=out.text.map(text_hash)
    out['sample_id']=[f'{key}:{i}:{h[:16]}' for i,h in enumerate(out.text_sha256)]
    return out

def read_benchmark(c,name,relative_path):
    """Load one broad LangID benchmark and retain the eleven reported groups."""
    path=resolve(c,relative_path)
    if not path.exists():
        raise FileNotFoundError(f'Missing {path}. Put the three benchmark JSONL files in data/preprocessed/.')
    raw=pd.read_json(path,lines=True,dtype=False).fillna('').astype(str)
    cols=c['columns']
    missing={cols['text'],cols['label']}-set(raw.columns)
    if missing: raise ValueError(f'{path.name}: missing columns {missing}')
    rows=[];empty_selected_removed=0
    for original_index,(text,label) in enumerate(zip(raw[cols['text']],raw[cols['label']])):
        text=clean_text(text,c['normalization'])
        raw_label=str(label).removeprefix('__label__').strip()
        mapped=canonical_label(raw_label,c.get('label_aliases'))
        # The benchmark label `san` can contain both Sinhala and Devanagari rows.
        if raw_label in {'sa','san','sanskrit'} or mapped in {'san_Sinh','san_Deva'}:
            has_sinh=any(0x0D80<=ord(ch)<=0x0DFF for ch in text)
            has_deva=any(0x0900<=ord(ch)<=0x097F for ch in text)
            mapped='san_Sinh' if has_sinh else 'san_Deva' if has_deva else mapped
        # FLORES+ tags romanized Arabic as `arb` too; arb_Arab is Arabic script only.
        if mapped=='arb_Arab' and not any(0x0600<=ord(ch)<=0x06FF or 0x0750<=ord(ch)<=0x077F
                                          or 0xFB50<=ord(ch)<=0xFDFF or 0xFE70<=ord(ch)<=0xFEFF
                                          for ch in text):
            continue
        if mapped in LANGUAGES:
            if not text: empty_selected_removed+=1
            else: rows.append((original_index,text,mapped))
    out=pd.DataFrame(rows,columns=['original_index','text','label'])
    if out.empty: raise ValueError(f'{path.name}: none of the eleven configured groups were found')
    out['text_sha256']=out.text.map(text_hash)
    conflicts=out.groupby('text_sha256').label.nunique()
    conflicts=conflicts[conflicts>1]
    conflicting_rows=int(out.text_sha256.isin(conflicts.index).sum())
    if len(conflicts): out=out.loc[~out.text_sha256.isin(conflicts.index)].copy()
    before=len(out)
    out=out.drop_duplicates('text_sha256',keep='first').copy()
    duplicates_removed=before-len(out)
    got=set(out.label)
    # A benchmark may legitimately lack a category: WiLI-2018 carries only the
    # `ara` macrolanguage, so it has no Modern Standard Arabic rows once
    # arb_Arab is restricted to `arb`. Such cases must be declared in
    # config['benchmark_absent_categories'][name]; anything else still aborts,
    # because a silently vanishing category is normally an alias/script bug.
    allowed=set((c.get('benchmark_absent_categories') or {}).get(name,[]))
    missing=set(LANGUAGES)-got
    if missing-allowed:
        raise ValueError(f'{path.name}: expected all eleven groups after ambiguity cleaning; missing {missing-allowed}')
    if missing:
        print(f'{path.name}: NOTE {sorted(missing)} absent by declaration; scored over {len(got)} categories')
    out['sample_id']=[f'benchmark:{name}:{i}:{h[:16]}' for i,h in zip(out.original_index,out.text_sha256)]
    cleaning={'same_label_duplicates_removed':duplicates_removed,
              'conflicting_text_types_removed':len(conflicts),
              'conflicting_rows_removed':conflicting_rows,
              'empty_rows_removed':empty_selected_removed}
    return out.drop(columns='original_index'),len(raw),cleaning

def prepare(c):
    keys=['train','validation','target_test','mixed_train','mixed_validation']
    data={k:read_data(c,k) for k in keys}
    for key,labels in [('train',TARGET),('validation',TARGET),('target_test',TARGET),
                       ('mixed_train',LANGUAGES),('mixed_validation',LANGUAGES)]:
        got=set(data[key].label)
        if got!=set(labels): raise ValueError(f'{key}: expected {labels}; missing {set(labels)-got}, unexpected {got-set(labels)}. Use explicit language_script labels.')
    # Target files are intentionally contained in their corresponding mixed files.
    # Cross-role overlap (train/validation/test) is still forbidden.
    report={'files':{},'checks':[], 'normalization':c['normalization']}
    for key,df in data.items():
        if df.text_sha256.duplicated().any():
            raise ValueError(f'{key}: duplicate normalized texts. Resolve conflicting labels and deduplicate before running.')
        report['files'][key]={'sha256':digest(resolve(c,c['data'][key])),
           'rows':len(df),'counts':df.label.value_counts().to_dict(),
           'document_ids_present':'doc_id' in df}
    for i,a in enumerate(keys):
        for b in keys[i+1:]:
            overlap=set(data[a].text_sha256)&set(data[b].text_sha256)
            role=lambda k:'train' if k in ['train','mixed_train'] else 'dev' if 'validation' in k else 'test'
            if role(a)!=role(b) and overlap:
                raise ValueError(f'Text leakage: {len(overlap)} shared texts between {a} and {b}')
            if role(a)!=role(b) and 'doc_id' in data[a] and 'doc_id' in data[b]:
                common=(set(data[a].doc_id)-{''})&(set(data[b].doc_id)-{''})
                if common and c['require_document_ids']:
                    raise ValueError(f'Document leakage: {a}/{b}, e.g. {sorted(common)[:3]}')
                if common:
                    report['checks'].append(f'{a}/{b}: WARNING {len(common)} shared group IDs (strict group check disabled)')
            if role(a)==role(b):
                report['checks'].append(f'{a}/{b}: same-role overlap allowed ({len(overlap)} exact texts)')
            else:
                report['checks'].append(f'{a}/{b}: no exact normalized text overlap')
    benchmarks={}
    for name,path in c['data']['benchmarks'].items():
        frame,original_rows,cleaning=read_benchmark(c,name,path)
        benchmarks[name]=frame
        report['files']['benchmark_'+name]={'sha256':digest(resolve(c,path)),'rows':len(frame),
            'original_rows':original_rows,'counts':frame.label.value_counts().to_dict(),
            **cleaning,'document_ids_present':False}
        if cleaning['same_label_duplicates_removed']:
            report['checks'].append(f"benchmark:{name}: removed {cleaning['same_label_duplicates_removed']} repeated texts with the same label")
        if cleaning['conflicting_text_types_removed']:
            report['checks'].append(f"benchmark:{name}: removed all {cleaning['conflicting_rows_removed']} rows belonging to {cleaning['conflicting_text_types_removed']} texts with conflicting labels")
        if cleaning['empty_rows_removed']:
            report['checks'].append(f"benchmark:{name}: removed {cleaning['empty_rows_removed']} empty/format-only rows")
        # Benchmark rows are held out from every train/validation pool.
        for key in ['train','validation','mixed_train','mixed_validation']:
            overlap=set(data[key].text_sha256)&set(frame.text_sha256)
            if overlap:
                data[key]=data[key].loc[~data[key].text_sha256.isin(overlap)].reset_index(drop=True)
                report['checks'].append(f'{key}/benchmark:{name}: dropped {len(overlap)} rows sharing text with the benchmark')
            else:
                report['checks'].append(f'{key}/benchmark:{name}: no exact normalized text overlap')
    # Generic Sanskrit aliases mean Sinhala-script Sanskrit only. Catch wrong files.
    for key,df in data.items():
        for label,range_ in [('sin_Sinh',(0x0D80,0x0DFF)),('pli_Sinh',(0x0D80,0x0DFF)),
                              ('san_Sinh',(0x0D80,0x0DFF)),('san_Deva',(0x0900,0x097F))]:
            texts=df.loc[df.label==label,'text']
            if texts.empty: continue
            bad=int((~texts.map(lambda text:any(range_[0]<=ord(ch)<=range_[1] for ch in text)).astype(bool)).sum())
            if bad:
                message=f'{key}: WARNING {bad} {label} rows have no characters from the expected script'
                if c.get('strict_script_check',False): raise ValueError(message.replace('WARNING ',''))
                report['checks'].append(message)
    out=resolve(c,c['output_dir']);out.mkdir(parents=True,exist_ok=True)
    (out/'data_audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    data['benchmarks']=benchmarks
    data['audit']=report
    return data

def write_fasttext(df,path):
    with open(path,'w',encoding='utf8') as f:
        for r in df.itertuples(): f.write(f'__label__{r.label} {r.text}\n')
