"""Short-text stress-test sets: k-word fragments of the target test split
(config `fragments`, method in lidpipe/fragments.py).

Outputs, in datasets/target_fragments/:
  target_test_<k>w.jsonl   one fragment per target test row (same sample_id and label)
  fragments_report.json    rows per label, rows kept whole (<= k words), length stats
"""
import json
from collections import Counter

import numpy as np

from lidpipe import config, fragments, paths
from lidpipe.manifest import prepare_output, write_manifest
from lidpipe.text import text_sha256

cfg = config.pipeline()['fragments']
with open(paths.TARGET / 'test' / 'test.jsonl', encoding='utf-8') as f:
    test = [json.loads(line) for line in f]

report = {'config': cfg, 'source_rows': len(test), 'sets': {}}
files = []
for k in fragments.sizes():
    rows, whole = [], Counter()
    for r in test:
        text = fragments.fragment(r['text'], k, cfg['seed'], r['sample_id'])
        if len(fragments.words_of(r['text'])) <= k:
            whole[r['label']] += 1
        rows.append({'sample_id': r['sample_id'], 'text': text, 'label': r['label'],
                     'text_sha256': text_sha256(text), 'flags': [], 'words': k,
                     'source_text_sha256': r['text_sha256']})
    path = prepare_output(fragments.path(k))
    with open(path, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    files.append(path)
    n_words = np.array([len(r['text'].split()) for r in rows])
    report['sets'][fragments.name(k)] = {
        'rows': len(rows), 'labels': dict(Counter(r['label'] for r in rows)),
        'kept_whole_short_sentences': dict(whole),
        'words_per_fragment': {'mean': round(float(n_words.mean()), 3), 'min': int(n_words.min()),
                               'max': int(n_words.max())},
        'distinct_texts': len({r['text_sha256'] for r in rows})}
    print(f'{fragments.name(k)}: {len(rows)} rows, {sum(whole.values())} sentences already <= {k} words '
          f'(kept whole), mean {n_words.mean():.2f} words', flush=True)
rpath = prepare_output(paths.FRAGMENTS / 'fragments_report.json')
rpath.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
files.append(rpath)
write_manifest(paths.FRAGMENTS, '03.prepare_datasets.fragments', files)
