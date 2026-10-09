"""CommonLID test set (one JSONL per language tag), pinned revision."""
from lidpipe import paths
from lidpipe.download import finish, hf_snapshot

out = paths.benchmark_raw('commonlid')
lock, files = hf_snapshot('commonlid', out, ['data/*.jsonl'])
finish(out, 'commonlid', lock, files)
