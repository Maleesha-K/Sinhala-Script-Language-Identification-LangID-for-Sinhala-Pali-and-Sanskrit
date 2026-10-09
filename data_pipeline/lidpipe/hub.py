"""Hugging Face repo naming for artefacts this project publishes.

Our own repos are named from environment variables, so a fork can publish to
its own organisation without editing code:

    HF_ORG               organisation/user that owns our repos (default: script-langid)
    HF_TARGET_DATASET    name of the target-language dataset   (default: sinhala-script-lid)
    HF_PUBLISH_PRIVATE   1 = create new repos as private        (default: 1)

Lock entries may use `{HF_ORG}` / `{HF_TARGET_DATASET}` in `repo_id`. A pinned
`revision` is only meaningful for the repo it was published to
(`published_repo`); for any other repo the files are still verified against
their pinned sha256, so a re-hosted copy must be byte-identical.
"""
import os

from .env import flag, load_env

DEFAULTS = {'HF_ORG': 'script-langid', 'HF_TARGET_DATASET': 'sinhala-script-lid'}


def setting(name):
    load_env()
    return os.environ.get(name, '').strip() or DEFAULTS[name]


def target_dataset_repo():
    return f'{setting("HF_ORG")}/{setting("HF_TARGET_DATASET")}'


def publish_private():
    load_env()
    return flag('HF_PUBLISH_PRIVATE', True)


def resolve(lock):
    """Return (repo_id, revision) for a lock entry, expanding env placeholders."""
    repo = lock['repo_id'].format(**{k: setting(k) for k in DEFAULTS})
    revision = lock.get('revision')
    if lock.get('published_repo') and lock['published_repo'] != repo:
        revision = None  # different host: rely on the sha256 pins instead
    return repo, revision
