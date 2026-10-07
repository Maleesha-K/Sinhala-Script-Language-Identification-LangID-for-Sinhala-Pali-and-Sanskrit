"""Every filesystem location used by the pipeline, relative to data_pipeline/."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONFIG_DIR = ROOT / 'config'
PIPELINE_CONFIG = CONFIG_DIR / 'pipeline.yaml'
LABELS_CONFIG = CONFIG_DIR / 'labels.yaml'
LOCKS = CONFIG_DIR / 'locks.json'
REFERENCE_OUTPUTS = CONFIG_DIR / 'reference_outputs.json'
ENV_FILE = ROOT / '.env'
ENV_EXAMPLE = ROOT / '.env.example'

SCRIPTS = ROOT / 'scripts'
STATE_DIR = ROOT / '.state'
LOGS_DIR = ROOT / 'logs'

DATASETS = ROOT / 'datasets'
TARGET = DATASETS / 'target_language'
BENCHMARKS = DATASETS / 'hybrid_benchmark'
FINETUNE = DATASETS / 'hybrid_finetune'
RESULTS = DATASETS / 'benchmark_results'

MODELS = ROOT / 'models'

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
