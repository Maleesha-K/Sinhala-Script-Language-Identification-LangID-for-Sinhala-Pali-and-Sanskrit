"""One place that decides where PyTorch models run (LID-176 leaf surgery,
ConLID, XLM-R, Char-CNN/BiGRU). fastText-native models and the sklearn/XGBoost
baselines always run on CPU.

PIPELINE_DEVICE (in .env):  auto (default) -> CUDA when usable, else CPU
                            cuda           -> CUDA or fail
                            cpu            -> CPU even if a GPU exists
"""
import os
import shutil
import subprocess
from functools import lru_cache

from .env import load_env


def nvidia_gpus():
    """GPU names reported by the NVIDIA driver (empty list if none / no driver)."""
    exe = shutil.which('nvidia-smi')
    if not exe:
        return []
    try:
        out = subprocess.run([exe, '--query-gpu=name,driver_version,memory.total', '--format=csv,noheader'],
                             capture_output=True, text=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def diagnose():
    """Facts preflight needs to explain any CPU/GPU mismatch."""
    info = {'setting': setting(), 'nvidia_gpus': nvidia_gpus()}
    try:
        import torch
    except ImportError:
        return {**info, 'torch': None}
    info.update(torch=torch.__version__, torch_cuda_build=torch.version.cuda,
                cuda_available=torch.cuda.is_available())
    if info['cuda_available']:
        p = torch.cuda.get_device_properties(0)
        info['device_name'], info['device_gib'] = p.name, round(p.total_memory / 2 ** 30, 1)
    return info


def setting():
    load_env()
    value = os.environ.get('PIPELINE_DEVICE', 'auto').strip().lower() or 'auto'
    if value not in {'auto', 'cuda', 'cpu'}:
        raise SystemExit(f'PIPELINE_DEVICE={value!r}: use auto, cuda or cpu')
    return value


@lru_cache(maxsize=None)
def torch_device():
    """'cuda' or 'cpu' for every PyTorch model in this process."""
    import torch
    want = setting()
    if want == 'cpu':
        return 'cpu'
    if torch.cuda.is_available():
        return 'cuda'
    if want == 'cuda':
        raise SystemExit('PIPELINE_DEVICE=cuda but PyTorch cannot use a GPU; run '
                         '`uv run python run_pipeline.py --preflight-only` for the diagnosis')
    return 'cpu'
