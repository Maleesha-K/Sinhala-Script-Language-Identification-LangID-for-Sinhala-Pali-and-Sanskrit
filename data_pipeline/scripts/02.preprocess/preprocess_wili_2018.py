"""WiLI-2018 TEST split only -> clean.jsonl / eval.jsonl.

WiLI codes are kept as-is except the overrides in config/labels.yaml (`als`
means Alemannic, ISO gsw). WiLI only has macrolanguage `ara`, so it has no
arb_Arab rows (declared absent). The script is derived per language.
"""
from lidpipe import config, paths
from lidpipe.benchmarks import build

raw = paths.benchmark_raw('wili_2018')
# Split on '\n' only: str.splitlines() would also split on U+2028/U+0085 inside
# a paragraph and misalign texts with labels.
texts = (raw / 'x_test.txt').read_text(encoding='utf-8').split('\n')
labels = (raw / 'y_test.txt').read_text(encoding='utf-8').split('\n')
if texts[-1] == '' and labels[-1] == '':
    texts, labels = texts[:-1], labels[:-1]
if len(texts) != len(labels):
    raise SystemExit(f'x_test has {len(texts)} lines but y_test has {len(labels)}')


def rows():
    for i, (text, label) in enumerate(zip(texts, labels)):
        yield {'sample_id': f'wili_2018:test:{i}', 'text': text, 'label_raw': label.strip()}


build('wili_2018', rows(), expected_rows=config.locks()['wili_2018']['expected_rows'])
