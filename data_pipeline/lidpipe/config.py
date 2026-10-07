"""Load pipeline.yaml / labels.yaml / locks.json and hash them for resume checks."""
import hashlib
import json
from functools import lru_cache

import yaml

from . import paths


@lru_cache(maxsize=None)
def pipeline():
    return yaml.safe_load(paths.PIPELINE_CONFIG.read_text(encoding='utf-8'))


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
