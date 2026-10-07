"""Stage registry: what each stage runs, needs, reads and writes."""
import hashlib
import json
from dataclasses import dataclass, field

from . import config, paths

BENCH_DIRS = [paths.benchmark_dir(n) for n in paths.BENCHMARK_NAMES]
BENCH_RAW = [paths.benchmark_raw(n) for n in paths.BENCHMARK_NAMES]
OPENLID_RAW = paths.FINETUNE / 'openlid_v2' / 'raw'
REPLAY_MIXED = paths.FINETUNE / 'replay_mixed'


@dataclass
class Stage:
    id: str
    name: str
    steps: list                      # scripts, relative to scripts/, run in order
    needs_locks: list = field(default_factory=list)   # keys in config/locks.json
    needs_tools: list = field(default_factory=list)
    needs_gpu: bool = False
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
        scope = {'locks': {k: config.locks()[k] for k in self.needs_locks},
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
    ], disk_gb=2, inputs=BENCH_RAW, outputs=BENCH_DIRS, uses_labels=True, pipeline_keys=['preprocess'],
       reports=[d / 'manifest.json' for d in BENCH_DIRS]),
    Stage('05', 'prepare_datasets', ['05.prepare_datasets/prepare_replay.py'],
          disk_gb=2, inputs=BENCH_DIRS + [paths.TARGET, OPENLID_RAW], outputs=[REPLAY_MIXED],
          uses_labels=True, pipeline_keys=['replay', 'target_split'],
          reports=[REPLAY_MIXED / 'replay_report.json']),
    Stage('03', 'dataset_checking', ['03.dataset_checking/check_datasets.py'],
          inputs=BENCH_DIRS + [paths.TARGET, REPLAY_MIXED], outputs=[paths.DATASETS / 'audit'],
          uses_labels=True, pipeline_keys=['preprocess', 'target_split', 'replay'],
          reports=[paths.DATASETS / 'audit' / 'audit_report.md']),
    Stage('00', 'traditional_baselines', [], implemented=False),
    Stage('04', 'benchmark_zero_shot', [], implemented=False),
    Stage('06', 'train_models', [], implemented=False),
    Stage('07', 'benchmark_evaluation', [], implemented=False),
]

# Execution order follows dependencies, not numbering: dataset checking (03)
# audits everything including the replay data from 05, and the baselines (00)
# train on the checked splits.
ORDER = ['01', '02', '05', '03', '00', '04', '06', '07']
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
