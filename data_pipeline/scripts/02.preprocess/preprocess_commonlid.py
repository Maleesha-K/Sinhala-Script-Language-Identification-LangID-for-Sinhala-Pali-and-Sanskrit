"""CommonLID test -> clean.jsonl / eval.jsonl.

`tag` is kept as the ISO 639-3 code without macrolanguage merging: `ara` and
`arb` stay distinct (only `arb` is scored as arb_Arab), as do zho/cmn, msa/zsm,
swa/swh. CommonLID has no script tag, so the script is derived per language
(see lidpipe.benchmarks).
"""
import json

from lidpipe import config, paths
from lidpipe.benchmarks import build


def rows():
    for f in sorted((paths.benchmark_raw('commonlid') / 'data').glob('*.jsonl')):
        with open(f, encoding='utf-8') as fh:
            for line in fh:
                r = json.loads(line)
                yield {'sample_id': f'commonlid:{r["line_id"]}', 'text': r['text'],
                       'label_raw': r['tag'], 'meta': {'line_id': r['line_id']}}


build('commonlid', rows(), expected_rows=config.locks()['commonlid']['expected_rows'])
