"""Fine-tune every model in both phases with the shared protocol
(lidpipe/training.py, config `training`).

A (model, phase, seed) whose chosen.json matches the current protocol hash is
skipped, so an interrupted run resumes where it stopped. GPU-only models are
skipped (and recorded) when SKIP_GPU_MODELS=1 and no CUDA device is present.
"""
import hashlib
import json

from lidpipe import config, paths
from lidpipe.env import flag, load_env
from lidpipe.manifest import sha256_file, write_manifest
from lidpipe.models import REGISTRY, base_checkpoint, selected
from lidpipe.models.trainers import TRAINERS
from lidpipe.training import PHASE_DIRS, model_dir, select

load_env()
cfg = config.pipeline()
MODELS = ['nllb_lid218', 'glotlid_v3', 'openlid_v3', 'lid176', 'conlid', 'xlmr']
GPU_ONLY = {'xlmr'}


def protocol_hash(family):
    data = [paths.TARGET / 'manifest.json', paths.FINETUNE / 'replay_mixed' / 'manifest.json']
    blob = {'training': {k: v for k, v in cfg['training'].items() if k != 'lr_grid'},
            'grid': cfg['training']['lr_grid'][family], 'smoke': cfg.get('smoke', False),
            'data': [sha256_file(p) for p in data]}
    return hashlib.sha256(json.dumps(blob, sort_keys=True).encode()).hexdigest()


def make_trainer(family, base_path, labels, seed, tcfg):
    return TRAINERS[family](base_path, labels, seed, tcfg)


def cuda():
    import torch
    return torch.cuda.is_available()


import os  # noqa: E402

explicit = set(filter(None, os.environ.get('PIPELINE_MODELS', '').split(',')))
deferred = [m for m in cfg['training'].get('deferred_models', []) if m not in explicit]
skipped = [f'{m}: deferred (config training.deferred_models); run with --only 07 --models {m}'
           for m in deferred]
for phase in ('target_only', 'rehearsal'):
    for model in [m for m in selected(MODELS) if m not in deferred]:
        family = REGISTRY[model][0]
        if model in GPU_ONLY and not cuda():
            if flag('SKIP_GPU_MODELS'):
                skipped.append(f'{model}/{phase}: no CUDA device (SKIP_GPU_MODELS=1)')
                continue
            raise SystemExit(f'{model} needs a CUDA GPU; set SKIP_GPU_MODELS=1 to skip it')
        for seed in cfg['seeds']:
            chosen_file = model_dir(phase, model, seed) / 'chosen.json'
            h = protocol_hash(family)
            if (not flag('PIPELINE_FORCE') and chosen_file.exists()
                    and json.loads(chosen_file.read_text()).get('protocol_sha256') == h):
                print(f'{model} {phase} seed={seed}: already trained with this protocol, skipping', flush=True)
                continue
            chosen = select(model, family, base_checkpoint(model), phase, seed, make_trainer)
            chosen['protocol_sha256'] = h
            chosen_file.write_text(json.dumps(chosen, indent=2) + '\n', encoding='utf-8')

for phase, d in PHASE_DIRS.items():
    root = paths.MODELS / d
    if root.exists():
        files = sorted(p for p in root.rglob('*') if p.is_file() and p.name != 'manifest.json')
        write_manifest(root, f'07.train_models.{phase}', files, extra={'skipped': skipped}, readonly=False)
for s in skipped:
    print('SKIPPED', s)
