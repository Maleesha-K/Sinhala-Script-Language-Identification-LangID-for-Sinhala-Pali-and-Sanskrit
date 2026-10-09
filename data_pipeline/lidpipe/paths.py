"""Every filesystem location used by the pipeline, relative to data_pipeline/."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONFIG_DIR = ROOT / 'config'
PIPELINE_CONFIG = CONFIG_DIR / 'pipeline.yaml'
LABELS_CONFIG = CONFIG_DIR / 'labels.yaml'
LOCKS = CONFIG_DIR / 'locks.json'
REFERENCE_OUTPUTS = CONFIG_DIR / 'reference_outputs.json'
ENV_FILE = ROOT / '.env'
ENV_EXAMPLE = ROOT / '.env.example'

# Smoke runs (run_pipeline.py --smoke) write models, results and stage state
# under smoke/ so they can never be mistaken for, or overwrite, real results.
SMOKE = os.environ.get('PIPELINE_SMOKE', '').strip() in {'1', 'true', 'yes'}
_OUT = ROOT / 'smoke' if SMOKE else ROOT

SCRIPTS = ROOT / 'scripts'
STATE_DIR = _OUT / '.state'
LOGS_DIR = ROOT / 'logs'

DATASETS = ROOT / 'datasets'
TARGET = DATASETS / 'target_language'
FRAGMENTS = DATASETS / 'target_fragments'      # k-word fragments of the target test split
BENCHMARKS = DATASETS / 'hybrid_benchmark'
FINETUNE = DATASETS / 'hybrid_finetune'
RESULTS = _OUT / 'datasets' / 'benchmark_results'

MODELS = _OUT / 'models'
PRETRAINED = ROOT / 'models' / 'pretrained'   # downloaded base checkpoints (shared)

BENCHMARK_NAMES = ('flores_plus', 'wili_2018', 'commonlid')


def benchmark_dir(name):
    return BENCHMARKS / name


def benchmark_raw(name):
    return BENCHMARKS / name / 'raw'


def benchmark_clean(name):
    """All languages, normalised, deduplicated, with flags."""
    return BENCHMARKS / name / 'clean.jsonl'


def benchmark_eval(name):
    """The scored 11-label subset that every model is evaluated on."""
    return BENCHMARKS / name / 'eval.jsonl'
