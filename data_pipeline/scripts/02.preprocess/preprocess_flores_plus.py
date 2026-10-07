"""FLORES+ devtest -> clean.jsonl / eval.jsonl.

Labels are `<iso_639_3>_<iso_15924>` from the dataset's own fields, so romanised
Arabic (arb_Latn) stays separate from arb_Arab and native sin_Sinh / san_Deva
rows are kept. Regional variants sharing language+script (e.g. apc nort/sout)
keep their glottocode/variant as metadata.
"""
import json

from lidpipe import config, paths
from lidpipe.benchmarks import build


def rows():
    for f in sorted((paths.benchmark_raw('flores_plus') / 'devtest').glob('*.jsonl')):
        with open(f, encoding='utf-8') as fh:
            for line in fh:
                r = json.loads(line)
                variant = f.stem  # e.g. apc_Arab_nort3139, nob_Latn_radical
                yield {'sample_id': f'flores_plus:{variant}:{r["id"]}', 'text': r['text'],
                       'label_raw': r['iso_639_3'], 'script': r['iso_15924'],
                       'meta': {'glottocode': r['glottocode'], 'variant': r['variant'] or None,
                                'flores_id': r['id']}}


build('flores_plus', rows(), expected_rows=config.locks()['flores_plus']['expected_rows'])
