"""FLORES+ devtest (all language-script variants), pinned revision."""
from lidpipe import paths
from lidpipe.download import finish, hf_snapshot

out = paths.benchmark_raw('flores_plus')
lock, files = hf_snapshot('flores_plus', out, ['devtest/*.jsonl'])
finish(out, 'flores_plus', lock, files)
