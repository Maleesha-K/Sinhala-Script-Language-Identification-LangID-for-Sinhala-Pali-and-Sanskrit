"""Checks run before any stage, each failing with a message that says how to fix it."""
import os
import shutil
import sys
import urllib.request

from . import config, hub, paths
from .env import flag, load_env, parse_env


class Check:
    def __init__(self):
        self.results = []  # (status, name, detail) with status in ok/warn/fail

    def ok(self, name, detail=''):
        self.results.append(('ok', name, detail))

    def warn(self, name, detail):
        self.results.append(('warn', name, detail))

    def fail(self, name, detail):
        self.results.append(('fail', name, detail))

    @property
    def failed(self):
        return any(s == 'fail' for s, _, _ in self.results)

    def report(self):
        mark = {'ok': '  OK  ', 'warn': ' WARN ', 'fail': ' FAIL '}
        return '\n'.join(f'[{mark[s]}] {n}' + (f'\n         {d}' if d else '') for s, n, d in self.results)


def _python(c):
    if sys.version_info >= (3, 12):
        c.ok('Python >= 3.12', sys.version.split()[0])
    else:
        c.fail('Python >= 3.12', f'found {sys.version.split()[0]}; run through `uv run python run_pipeline.py`')


def _env_file(c):
    if not paths.ENV_FILE.exists():
        c.fail('.env present', f'copy {paths.ENV_EXAMPLE.name} to .env and fill in the values '
                               f'(cp .env.example .env)')
        return
    example = set(parse_env(paths.ENV_EXAMPLE)) if paths.ENV_EXAMPLE.exists() else set()
    missing = sorted(k for k in example if not os.environ.get(k) and k in _required_env())
    if missing:
        c.fail('.env complete', f'missing required keys: {", ".join(missing)} (see .env.example)')
    else:
        c.ok('.env present')


def _required_env():
    return {'HF_TOKEN'}


def _hf(c, repos):
    token = os.environ.get('HF_TOKEN', '').strip()
    if not token or token.startswith('your_'):
        c.fail('HF_TOKEN set', 'create a read token at https://huggingface.co/settings/tokens and put it in .env')
        return
    if not token.startswith('hf_'):
        c.warn('HF_TOKEN format', 'Hugging Face tokens normally start with "hf_"')
    try:
        from huggingface_hub import HfApi
        from huggingface_hub.errors import GatedRepoError, RepositoryNotFoundError
    except ImportError:
        c.fail('huggingface_hub installed', 'run `uv sync`')
        return
    api = HfApi(token=token)
    try:
        user = api.whoami()['name']
        c.ok('HF_TOKEN valid', f'authenticated as {user}')
    except Exception as e:  # noqa: BLE001 - surface any auth/network error verbatim
        c.fail('HF_TOKEN valid', f'whoami failed: {type(e).__name__}: {str(e)[:200]}')
        return
    for key, lock in repos.items():
        (repo, rev), kind = hub.resolve(lock), lock['kind']
        url = f'https://huggingface.co/{"datasets/" if kind == "dataset" else ""}{repo}'
        try:
            info = (api.dataset_info if kind == 'dataset' else api.model_info)(repo, revision=rev)
            files = {s.rfilename for s in info.siblings or []}
            need = [f for f in lock.get('files', []) if f not in files]
            if need:
                c.fail(f'access {repo}', f'pinned revision lacks {need}')
                continue
            # *_info succeeds on gated repos even when the terms were not
            # accepted, so download one small file to prove real access.
            if lock.get('probe_file'):
                api.hf_hub_download(repo, lock['probe_file'], revision=rev,
                                    repo_type='dataset' if kind == 'dataset' else None,
                                    local_dir=paths.STATE_DIR / 'probe' / key)
            c.ok(f'access {repo}', f'revision {rev[:10] if rev else "latest"}')
        except GatedRepoError:
            c.fail(f'access {repo}', f'gated: log in and accept the terms at {url}')
        except RepositoryNotFoundError:
            c.fail(f'access {repo}', f'not found or no permission: {url}')
        except Exception as e:  # noqa: BLE001
            c.fail(f'access {repo}', f'{type(e).__name__}: {str(e)[:200]}')


def _url(c, name, url):
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=20) as r:
            c.ok(f'reachable: {name}', f'HTTP {r.status}')
    except Exception as e:  # noqa: BLE001
        c.fail(f'reachable: {name}', f'{url}: {type(e).__name__}: {e}')


def _local_release(c, key, entry):
    """A dataset not yet published: only the maintainer's machine has it."""
    path = paths.ROOT / entry['path']
    missing = [f for f in entry['files_sha256'] if not (path / f).exists()]
    if missing:
        c.fail(f'{key} available', f'{key} is not published yet and {entry["path"]} lacks {missing}. '
                                   f'Ask the maintainers for the release, or (maintainers) run '
                                   f'scripts/maintainer/resplit_target.py')
    else:
        c.warn(f'{key} available', f'using the unpublished local release at {entry["path"]}; '
                                   f'publish it and pin the HF revision in config/locks.json')


def _tools(c, tools):
    for t in tools:
        if shutil.which(t):
            c.ok(f'tool: {t}')
        else:
            c.fail(f'tool: {t}', f'`{t}` not found on PATH; install it (e.g. build-essential / git)')


def _device(c, required):
    """Where PyTorch models will run, and why. An NVIDIA GPU that PyTorch cannot
    use is a FAIL (it silently costs hours), unless PIPELINE_DEVICE=cpu."""
    from . import device
    d = device.diagnose()
    gpus, name = d['nvidia_gpus'], 'compute device (PyTorch)'
    if d['torch'] is None:
        c.fail(name, 'PyTorch is not installed; run `uv sync`')
        return
    if d['setting'] == 'cpu':
        c.warn(name, f'PIPELINE_DEVICE=cpu: PyTorch models run on CPU (torch {d["torch"]})'
               + (f'; GPU present but unused: {gpus[0]}' if gpus else ''))
        return
    if d['cuda_available']:
        c.ok(name, f'CUDA: {d["device_name"]}, {d["device_gib"]} GiB (torch {d["torch"]}, CUDA build '
                   f'{d["torch_cuda_build"]})')
        return
    if gpus and d['torch_cuda_build'] is None:
        c.fail(name, f'an NVIDIA GPU is present ({gpus[0]}) but PyTorch is a CPU-only build '
                     f'(torch {d["torch"]}). Run `uv sync` to install the CUDA build pinned in uv.lock '
                     f'(on Windows: deactivate any other venv first), or set PIPELINE_DEVICE=cpu to run on CPU.')
    elif gpus:
        c.fail(name, f'NVIDIA GPU present ({gpus[0]}) and torch has CUDA {d["torch_cuda_build"]}, but CUDA '
                     f'is unusable: update the NVIDIA driver to one supporting CUDA {d["torch_cuda_build"]}, '
                     f'or set PIPELINE_DEVICE=cpu.')
    elif d['setting'] == 'cuda':
        c.fail(name, 'PIPELINE_DEVICE=cuda but no NVIDIA GPU/driver was found (nvidia-smi missing)')
    elif required and not flag('SKIP_GPU_MODELS'):
        c.fail(name, 'a selected model needs a CUDA GPU but none was found; set SKIP_GPU_MODELS=1 to skip it')
    else:
        c.warn(name, 'no NVIDIA GPU found: PyTorch models run on CPU (slower); GPU-only models are skipped')


def _disk(c, min_gb):
    paths.DATASETS.mkdir(exist_ok=True)
    free = shutil.disk_usage(paths.DATASETS).free / 2**30
    if free >= min_gb:
        c.ok('free disk', f'{free:.0f} GiB')
    else:
        c.fail('free disk', f'{free:.1f} GiB free; at least {min_gb} GiB needed for the selected stages')


def run(stages):
    """Run every check required by `stages` (a list of Stage objects)."""
    load_env()
    c = Check()
    _python(c)
    _env_file(c)
    locks = config.locks()
    repos = {}
    urls = {}
    tools, gpu, torch_stage, disk = set(), False, False, 0
    for s in stages:
        for key in s.needs_locks:
            entry = locks[key]
            if entry['kind'] == 'url':
                urls[key] = entry['url']
            elif entry['kind'] == 'local_release':
                _local_release(c, key, entry)
            else:
                repos[key] = entry
        tools |= set(s.needs_tools)
        gpu |= s.needs_gpu
        torch_stage |= s.uses_torch
        disk = max(disk, s.disk_gb)
    if repos:
        _hf(c, repos)
    for name, url in urls.items():
        _url(c, name, url)
    _tools(c, sorted(tools))
    if gpu or torch_stage:
        _device(c, gpu)
    _disk(c, disk)
    return c
