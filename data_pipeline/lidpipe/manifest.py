"""Write-once outputs: sha256 manifests that downstream stages verify."""
import hashlib
import json
import os
import shutil
import stat
from datetime import datetime, timezone
from pathlib import Path

from . import config, paths


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def make_readonly(path):
    mode = os.stat(path).st_mode
    os.chmod(path, mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


def reset_dir(path):
    """Delete a directory this stage owns (including read-only files) and recreate it."""
    path = Path(path)
    if path.exists():
        def _unlock(func, p, _exc):
            os.chmod(p, stat.S_IWRITE | stat.S_IREAD)
            func(p)
        shutil.rmtree(path, onexc=_unlock)
    path.mkdir(parents=True)
    return path


def prepare_output(path):
    """Allow a stage to replace its own previous (read-only) output."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        os.chmod(path, os.stat(path).st_mode | stat.S_IWUSR)
        path.unlink()
    return path


def write_manifest(directory, stage, files, extra=None, readonly=True):
    """Record sha256 + size of `files` (paths inside `directory`)."""
    directory = Path(directory)
    entries = {}
    for f in files:
        f = Path(f)
        entries[str(f.relative_to(directory))] = {'sha256': sha256_file(f), 'bytes': f.stat().st_size}
        if readonly:
            make_readonly(f)
    manifest = {'stage': stage, 'created_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                'config_sha256': config.config_hash(), 'files': entries, **(extra or {})}
    out = prepare_output(directory / 'manifest.json')
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return manifest


def read_manifest(directory):
    return json.loads((Path(directory) / 'manifest.json').read_text(encoding='utf-8'))


def verify_manifest(directory):
    """Return a list of problems (empty if every file matches its manifest)."""
    directory = Path(directory)
    if not (directory / 'manifest.json').exists():
        return [f'{directory.relative_to(paths.ROOT)}: no manifest.json']
    problems = []
    for name, entry in read_manifest(directory)['files'].items():
        f = directory / name
        if not f.exists():
            problems.append(f'{f.relative_to(paths.ROOT)}: missing')
        elif sha256_file(f) != entry['sha256']:
            problems.append(f'{f.relative_to(paths.ROOT)}: sha256 differs from manifest (file was modified)')
    return problems
