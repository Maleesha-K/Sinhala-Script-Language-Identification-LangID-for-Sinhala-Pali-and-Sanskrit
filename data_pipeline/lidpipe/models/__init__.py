"""Uniform model adapters. Every model exposes the same interface so stages
06-08 treat them identically:

    adapter = load(name, checkpoint=None)    # None -> pinned pretrained base
    labels, confidences = adapter.predict(texts)
    adapter.labels                           # raw output labels

Training goes through `lidpipe.training`, which drives each family's own
`train_epoch` with one shared selection protocol.
"""
import os
import urllib.request
from pathlib import Path

from .. import config, hub, paths
from ..env import load_env
from ..manifest import sha256_file

# name -> (family, lock key, file inside the repo)
REGISTRY = {
    'lid176': ('fasttext_hs', 'lid176', None),
    'openlid_v3': ('fasttext_softmax', 'openlid_v3', 'openlid-v3.bin'),
    'glotlid_v3': ('fasttext_softmax', 'glotlid_v3', 'model_v3.bin'),
    'nllb_lid218': ('fasttext_softmax', 'nllb_lid218', 'model.bin'),
    'conlid': ('conlid', 'conlid', None),
    'xlmr': ('xlmr', 'xlmr_lid', None),   # papluca/xlm-roberta-base-language-detection
}
PRETRAINED = ['lid176', 'openlid_v3', 'glotlid_v3', 'nllb_lid218', 'conlid', 'xlmr']  # all have a LID head


def selected(default):
    """Models chosen with `run_pipeline.py --models a,b` (env PIPELINE_MODELS),
    restricted to `default`; all of `default` when unset."""
    chosen = [m for m in os.environ.get('PIPELINE_MODELS', '').split(',') if m]
    if unknown := set(chosen) - set(REGISTRY) - {'nb', 'svm', 'logreg', 'xgboost', 'fasttext_scratch',
                                                   'char_cnn', 'char_bigru'}:
        raise SystemExit(f'unknown model(s) {sorted(unknown)}')
    return [m for m in default if not chosen or m in chosen]


def base_checkpoint(name):
    """Path of the pinned pretrained checkpoint (downloaded once, then cached)."""
    from huggingface_hub import hf_hub_download, snapshot_download
    load_env()
    family, key, filename = REGISTRY[name]
    lock = config.locks()[key]
    if lock['kind'] == 'url':
        dest = paths.PRETRAINED / name / Path(lock['url']).name
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            print(f'downloading {lock["url"]}', flush=True)
            urllib.request.urlretrieve(lock['url'], dest.with_suffix('.part'))
            dest.with_suffix('.part').rename(dest)
        if lock.get('sha256') and sha256_file(dest) != lock['sha256']:
            raise SystemExit(f'{dest}: sha256 differs from config/locks.json')
        return dest
    repo, revision = hub.resolve(lock)
    token = os.environ.get('HF_TOKEN')
    if filename:
        return Path(hf_hub_download(repo, filename, revision=revision, token=token))
    return Path(snapshot_download(repo, revision=revision, token=token, allow_patterns=lock.get('files')))


def load(name, checkpoint=None):
    family = REGISTRY[name][0]
    path = Path(checkpoint) if checkpoint else base_checkpoint(name)
    if family == 'fasttext_hs' and path.is_dir():  # fine-tuned LID-176 (leaf surgery)
        from .xlmr import LID176Continual
        return LID176Continual(path)
    if family.startswith('fasttext'):
        from .fasttext_native import NativeModel
        return NativeModel(path / 'model.bin' if path.is_dir() else path)
    if family == 'conlid':
        from .conlid import ConLID
        return ConLID(path)
    if family == 'xlmr':
        from .xlmr import XLMR
        return XLMR(path)
    raise ValueError(family)
