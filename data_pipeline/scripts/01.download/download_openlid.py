"""OpenLID-v2 training data for the 8 replay labels (rehearsal source)."""
from lidpipe import config, paths
from lidpipe.download import finish, hf_snapshot

out = paths.FINETUNE / 'openlid_v2' / 'raw'
lock, files = hf_snapshot('openlid_v2', out, config.locks()['openlid_v2']['files'])
finish(out, 'openlid_v2', lock, files)
