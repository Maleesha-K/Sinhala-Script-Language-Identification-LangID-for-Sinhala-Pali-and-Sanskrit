"""Stage registry: what each stage runs, needs, reads and writes."""
import hashlib
import json
import os
from dataclasses import dataclass, field

from . import config, paths

BENCH_DIRS = [paths.benchmark_dir(n) for n in paths.BENCHMARK_NAMES]
BENCH_RAW = [paths.benchmark_raw(n) for n in paths.BENCHMARK_NAMES]
OPENLID_RAW = paths.FINETUNE / 'openlid_v2' / 'raw'
REPLAY_MIXED = paths.FINETUNE / 'replay_mixed'
AUDIT = paths.DATASETS / 'audit'
# Model stages only start on data that passed the stage-04 audit.
CHECKED_DATA = BENCH_DIRS + [paths.TARGET, REPLAY_MIXED, paths.FRAGMENTS, AUDIT]


@dataclass
class Stage:
    id: str
    name: str
    steps: list                      # scripts, relative to scripts/, run in order
    needs_locks: list = field(default_factory=list)   # keys in config/locks.json
    needs_tools: list = field(default_factory=list)
    needs_gpu: bool = False                           # cannot run without CUDA
    uses_torch: bool = False                          # runs PyTorch models (GPU if usable)
    disk_gb: int = 1
    inputs: list = field(default_factory=list)        # dirs whose manifests must verify first
    outputs: list = field(default_factory=list)       # dirs whose manifests this stage writes
    uses_labels: bool = False                         # reads config/labels.yaml
    pipeline_keys: list = field(default_factory=list) # top-level keys of pipeline.yaml it reads
    reports: list = field(default_factory=list)       # human-readable outputs listed in the run summary
    deterministic: bool = True                        # outputs must match config/reference_outputs.json
    implemented: bool = True

    def config_hash(self):
        """Hash of only the configuration this stage reads, so unrelated config
        edits do not invalidate it."""
        scope = {'models': os.environ.get('PIPELINE_MODELS', ''),
                 'locks': {k: config.locks()[k] for k in self.needs_locks},
                 'labels': config.labels() if self.uses_labels else None,
                 'pipeline': {k: config.pipeline().get(k) for k in self.pipeline_keys}}
        return hashlib.sha256(json.dumps(scope, sort_keys=True).encode()).hexdigest()


STAGES = [
    Stage('01', 'download', [
        '01.download/download_flores_plus.py',
        '01.download/download_commonlid.py',
        '01.download/download_wili_2018.py',
        '01.download/download_target.py',
        '01.download/download_openlid.py',
    ], needs_locks=['flores_plus', 'commonlid', 'wili_2018', 'target_dataset', 'openlid_v2'], disk_gb=4,
       outputs=BENCH_RAW + [paths.TARGET, OPENLID_RAW],
       reports=[paths.TARGET / 'split_report.json']),
    Stage('02', 'preprocess', [
        '02.preprocess/preprocess_flores_plus.py',
        '02.preprocess/preprocess_commonlid.py',
        '02.preprocess/preprocess_wili_2018.py',
    ], disk_gb=2, inputs=BENCH_RAW + [paths.TARGET],   # target test is merged into each eval set
       outputs=BENCH_DIRS, uses_labels=True, pipeline_keys=['preprocess'],
       reports=[d / 'manifest.json' for d in BENCH_DIRS]),
    Stage('03', 'prepare_datasets', ['03.prepare_datasets/prepare_replay.py',
                                      '03.prepare_datasets/prepare_fragments.py'],
          disk_gb=2, inputs=BENCH_DIRS + [paths.TARGET, OPENLID_RAW], outputs=[REPLAY_MIXED, paths.FRAGMENTS],
          uses_labels=True, pipeline_keys=['replay', 'target_split', 'fragments'],
          reports=[REPLAY_MIXED / 'replay_report.json', paths.FRAGMENTS / 'fragments_report.json']),
    Stage('04', 'dataset_checking', ['04.dataset_checking/check_datasets.py'],
          inputs=BENCH_DIRS + [paths.TARGET, REPLAY_MIXED, paths.FRAGMENTS], outputs=[paths.DATASETS / 'audit'],
          uses_labels=True, pipeline_keys=['preprocess', 'target_split', 'replay', 'fragments'],
          reports=[paths.DATASETS / 'audit' / 'audit_report.md']),
    Stage('05', 'traditional_baselines', ['05.traditional_baselines/baselines.py'],
          disk_gb=4, inputs=CHECKED_DATA,
          outputs=[paths.MODELS / '00_traditional_ml_baselines', paths.RESULTS / '00_traditional_ml_baselines'],
          uses_labels=True, pipeline_keys=['baselines', 'training', 'seeds', 'smoke', 'bootstrap', 'fragments'],
          uses_torch=True, deterministic=False, reports=[paths.RESULTS / '00_traditional_ml_baselines' / 'manifest.json']),
    Stage('06', 'benchmark_zero_shot', ['06.benchmark_zero_shot/zero_shot.py'],
          needs_locks=['lid176', 'openlid_v3', 'glotlid_v3', 'nllb_lid218', 'conlid', 'xlmr_lid'], needs_tools=['g++'],
          disk_gb=6, inputs=CHECKED_DATA, outputs=[paths.RESULTS / '01_zero_shot'], uses_labels=True,
          pipeline_keys=['bootstrap', 'smoke'], uses_torch=True, deterministic=False,
          reports=[paths.RESULTS / '01_zero_shot' / 'manifest.json']),
    Stage('07', 'train_models', ['07.train_models/train_models.py'],
          needs_locks=['lid176', 'openlid_v3', 'glotlid_v3', 'nllb_lid218', 'conlid', 'xlmr_lid'],
          needs_tools=['g++'], disk_gb=12, inputs=CHECKED_DATA,
          outputs=[paths.MODELS / '02_target_only_sota', paths.MODELS / '03_global_rehearsal_sota'],
          uses_labels=True, pipeline_keys=['training', 'seeds', 'smoke'], uses_torch=True, deterministic=False,
          reports=[paths.MODELS / '02_target_only_sota' / 'manifest.json',
                   paths.MODELS / '03_global_rehearsal_sota' / 'manifest.json']),
    Stage('08', 'benchmark_evaluation', ['08.benchmark_evaluation/evaluate_finetuned.py',
                                          '08.benchmark_evaluation/make_tables.py'],
          inputs=CHECKED_DATA + [paths.MODELS / '02_target_only_sota', paths.MODELS / '03_global_rehearsal_sota',
                                 # tables also read the baseline and zero-shot results
                                 paths.RESULTS / '00_traditional_ml_baselines', paths.RESULTS / '01_zero_shot'],
          outputs=[paths.RESULTS / '02_target_only', paths.RESULTS / '03_multilingual_rehearsal',
                   paths.RESULTS / 'tables'],
          uses_labels=True, pipeline_keys=['bootstrap', 'seeds', 'smoke'], uses_torch=True, deterministic=False,
          reports=[paths.RESULTS / 'tables' / 'results.md']),
]

# Stage numbers are the execution order: datasets are prepared (03) before
# they are audited (04), and every model stage runs on audited data.
ORDER = ['01', '02', '03', '04', '05', '06', '07', '08']
BY_ID = {s.id: s for s in STAGES}


def select(spec=None, start=None, only=None):
    """Resolve CLI selection to an ordered list of stages."""
    named = set((only or '').split(',')) | set((spec or '').split('-')) | {start or ''}
    unknown = named - set(ORDER) - {''}
    if unknown:
        raise SystemExit(f'unknown stage(s): {sorted(unknown)}; valid: {ORDER}')
    ids = list(ORDER)
    if only:
        ids = [i for i in ORDER if i in set(only.split(','))]
    elif spec:
        # Ranges follow execution order, so 01-07 includes 00.
        lo, _, hi = spec.partition('-')
        ids = ORDER[ORDER.index(lo):ORDER.index(hi or lo) + 1]
    if start:
        ids = ids[ids.index(start):] if start in ids else []
    if not ids:
        raise SystemExit(f'no stages selected; ranges follow execution order {ORDER}')
    return [BY_ID[i] for i in ids]
