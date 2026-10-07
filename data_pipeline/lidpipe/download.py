"""Pinned downloads. Each writes raw files plus a manifest; nothing is transformed."""
import os
import shutil
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

import httpx

from . import config, hub
from .env import load_env
from .manifest import prepare_output, reset_dir, sha256_file, write_manifest

HF_RETRIES = 5  # waits 5, 10, 20, 40s between attempts


def hf_snapshot(lock_key, out_dir, patterns):
    """Download `patterns` from a pinned HF repo into `out_dir`, byte-for-byte."""
    from huggingface_hub import snapshot_download
    load_env()
    lock = config.locks()[lock_key]
    repo, revision = hub.resolve(lock)
    out_dir = reset_dir(out_dir)
    print(f'{repo} @ {revision[:10] if revision else "latest (sha256-verified)"} -> {out_dir}')
    # Connection resets (WinError 10054) are common on flaky links; retry without wiping
    # out_dir so files already fetched are skipped on the next attempt.
    for attempt in range(1, HF_RETRIES + 1):
        try:
            snapshot_download(repo, repo_type=lock['kind'], revision=revision,
                              allow_patterns=patterns, local_dir=out_dir, token=os.environ.get('HF_TOKEN'))
            break
        except httpx.TransportError as e:
            if attempt == HF_RETRIES:
                raise
            wait = 5 * 2 ** (attempt - 1)
            print(f'network error ({type(e).__name__}: {e}); retry {attempt}/{HF_RETRIES - 1} in {wait}s', flush=True)
            time.sleep(wait)
    shutil.rmtree(out_dir / '.cache', ignore_errors=True)  # hub bookkeeping, not data
    files = sorted(p for p in out_dir.rglob('*') if p.is_file())
    if not files:
        raise SystemExit(f'no files matched {patterns} in {repo}')
    return lock, files


def url_zip(lock_key, out_dir, members):
    """Download a zip, verify pinned member hashes, extract only `members`."""
    lock = config.locks()[lock_key]
    out_dir = reset_dir(out_dir)
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / 'archive.zip'
        print(f'{lock["url"]} -> {zpath}')
        urllib.request.urlretrieve(lock['url'], zpath)
        with zipfile.ZipFile(zpath) as zf:
            by_name = {Path(n).name: n for n in zf.namelist() if not n.endswith('/')}
            for m in members:
                if m not in by_name:
                    raise SystemExit(f'{m} not in archive (has {sorted(by_name)})')
                target = prepare_output(out_dir / m)
                with zf.open(by_name[m]) as src, open(target, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
    files = [out_dir / m for m in members]
    for f in files:
        want = lock.get('members_sha256', {}).get(f.name)
        if want and sha256_file(f) != want:
            raise SystemExit(f'{f.name}: sha256 does not match config/locks.json; the upstream file changed')
    return lock, files


def finish(out_dir, lock_key, lock, files):
    write_manifest(out_dir, '01.download', files, extra={'source': {lock_key: lock}})
    print(f'wrote {len(files)} files + manifest.json to {out_dir}')
