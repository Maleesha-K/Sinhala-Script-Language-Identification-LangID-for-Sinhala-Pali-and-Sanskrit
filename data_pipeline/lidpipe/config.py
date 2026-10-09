"""Load pipeline.yaml / labels.yaml / locks.json and hash them for resume checks."""
import hashlib
import json
import os
from functools import lru_cache

import yaml

from . import paths


@lru_cache(maxsize=None)
def pipeline():
    cfg = yaml.safe_load(paths.PIPELINE_CONFIG.read_text(encoding='utf-8'))
    # `run_pipeline.py --smoke` (env PIPELINE_SMOKE=1): tiny subsamples and one
    # grid point, to check the plumbing end to end in minutes.
    if os.environ.get('PIPELINE_SMOKE', '').strip() in {'1', 'true', 'yes'}:
        cfg['smoke'] = True
    return cfg


@lru_cache(maxsize=None)
def labels():
    return yaml.safe_load(paths.LABELS_CONFIG.read_text(encoding='utf-8'))


@lru_cache(maxsize=None)
def locks():
    return json.loads(paths.LOCKS.read_text(encoding='utf-8'))


def config_hash():
    """Hash of all three config files; a change invalidates completed stages."""
    h = hashlib.sha256()
    for p in (paths.PIPELINE_CONFIG, paths.LABELS_CONFIG, paths.LOCKS):
        h.update(p.read_bytes())
    return h.hexdigest()
