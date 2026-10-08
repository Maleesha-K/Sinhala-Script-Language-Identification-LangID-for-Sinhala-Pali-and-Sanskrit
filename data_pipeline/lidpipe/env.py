"""Minimal .env loader (KEY=VALUE lines); real environment variables win."""
import os

from . import paths


def parse_env(path):
    values = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        key = key.removeprefix('export ').strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in '"\'':
            value = value[1:-1]
        values[key] = value
    return values


def load_env(path=paths.ENV_FILE):
    """Load `.env` into os.environ without overriding variables already set."""
    if not path.exists():
        return {}
    values = parse_env(path)
    for k, v in values.items():
        os.environ.setdefault(k, v)
    return values


def flag(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in {'1', 'true', 'yes', 'on'}
