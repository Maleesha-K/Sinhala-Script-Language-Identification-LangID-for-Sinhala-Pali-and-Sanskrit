"""Where the fine-tuned checkpoints live.

data_pipeline stage 07 writes one checkpoint per model and phase to
data_pipeline/models/<phase dir>/<model>/seed<seed>/best/. The web app serves
the rehearsal phase (03_global_rehearsal_sota): it keeps the 8 replay
languages, so non-target text gets a real label instead of a forced target.

LANGID_FINETUNED_DIR replaces the phase directory (the Docker image mounts it
at /finetuned); LANGID_SEED picks the seed. Per-model *_MODEL_PATH variables
override single checkpoints.
"""

import os

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))

FINETUNED_DIR = os.environ.get("LANGID_FINETUNED_DIR") or os.path.join(
    _REPO_ROOT, "data_pipeline", "models", "03_global_rehearsal_sota"
)
SEED = os.environ.get("LANGID_SEED", "42")


def finetuned(model: str, *parts: str) -> str:
    """Path inside the selected checkpoint of a pipeline model (e.g. 'nllb_lid218')."""
    return os.path.join(FINETUNED_DIR, model, f"seed{SEED}", "best", *parts)
