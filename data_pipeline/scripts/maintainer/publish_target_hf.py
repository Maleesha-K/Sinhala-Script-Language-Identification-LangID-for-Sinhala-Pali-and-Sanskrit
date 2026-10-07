"""Publish the target release (datasets/target_release) to Hugging Face and pin
the published revision in config/locks.json. Maintainers only.

    uv run python scripts/maintainer/publish_target_hf.py

The repo is `$HF_ORG/$HF_TARGET_DATASET` (defaults: script-langid /
sinhala-script-lid; override in .env or with --repo). A new repo is created
private unless HF_PUBLISH_PRIVATE=0 (or --public). Requires a token with write
access to the organisation in HF_TOKEN. Uploaded files are byte-identical to
the local release, so the sha256 pins stay valid.
"""
import argparse
import json
import os

from lidpipe import config, hub, paths
from lidpipe.env import load_env
from lidpipe.manifest import sha256_file

CARD = """---
language: [si, pi, sa]
license: other
task_categories: [text-classification]
pretty_name: Sinhala-script LangID (Sinhala, Pali, Sanskrit)
configs:
  - config_name: default
    data_files:
      - {{split: train, path: train.jsonl}}
      - {{split: validation, path: validation.jsonl}}
      - {{split: test, path: test.jsonl}}
---

# Sinhala-script language identification: Sinhala, Pali, Sanskrit

Sentence-level instances of three languages written in Sinhala script, with a
leakage-free document-blocked split. Labels: `sin_Sinh`, `pli_Sinh`, `san_Sinh`.

## Rows

| split | sin_Sinh | pli_Sinh | san_Sinh | total |
|---|---:|---:|---:|---:|
{rows}

## Construction

Built by `scripts/maintainer/resplit_target.py` (config: `target_split` in
`config/pipeline.yaml`):

1. Sources pooled and NFC-normalised; text not in Sinhala script removed.
2. Documents: source document ids; for the Pali-Sinhala parallel corpus
   (sinhala-nlp/pali-sinhala, row-aligned) a sutta starts at each Pali incipit
   *evam me sutam*, and both sides of a translation pair share the document.
3. Split unit: contiguous block of <= {block_size} rows within a document.
4. Sentence-level units: split at sentence terminators, packed to <= {max_chars} characters.
5. Exact duplicates removed; texts with conflicting labels removed.
6. Near duplicates removed with MinHash LSH (character {shingle}-grams, Jaccard >= {threshold}).
7. Group-stratified {fractions} split (seed {seed}).

Leakage check: {leakage}

Length (characters): {lengths}

## Sources

{sources}

## Fields

`sample_id`, `text`, `label`, `source`, `subcorpus`, `doc_id`, `block_id`, `text_sha256`.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default=None, help='default: $HF_ORG/$HF_TARGET_DATASET')
    ap.add_argument('--public', action='store_true', help='create the repo public (default: HF_PUBLISH_PRIVATE)')
    args = ap.parse_args()
    load_env()
    from huggingface_hub import HfApi

    release = paths.DATASETS / 'target_release'
    pinned = config.locks()['target_dataset']['files_sha256']
    for name, sha in pinned.items():
        if sha256_file(release / name) != sha:
            raise SystemExit(f'{name} differs from config/locks.json; re-run resplit_target.py and update the lock')
    rep = json.loads((release / 'split_report.json').read_text(encoding='utf-8'))
    cfg = rep['config']
    rows = '\n'.join(
        f'| {s} | ' + ' | '.join(str(sum(rep['splits'][s].get(l, {}).values()))
                                for l in ('sin_Sinh', 'pli_Sinh', 'san_Sinh')) + f' | {rep["split_totals"][s]} |'
        for s in ('train', 'validation', 'test'))
    sources = {}
    for s in rep['splits'].values():
        for label, by_source in s.items():
            for src, n in by_source.items():
                sources.setdefault(src, {}).setdefault(label, 0)
                sources[src][label] += n
    card = CARD.format(rows=rows, block_size=cfg['block_size'], max_chars=cfg['max_chars'],
                       shingle=cfg['near_dup']['shingle'], threshold=cfg['near_dup']['threshold'],
                       fractions=cfg['fractions'], seed=cfg['seed'], leakage=rep['leakage'],
                       lengths=rep['length_chars'],
                       sources='\n'.join(f'- {src}: {labels}' for src, labels in sorted(sources.items())))
    (release / 'README.md').write_text(card, encoding='utf-8')

    repo = args.repo or hub.target_dataset_repo()
    private = not args.public and hub.publish_private()
    api = HfApi(token=os.environ['HF_TOKEN'])
    org = repo.split('/')[0]
    me = api.whoami()
    orgs = {o['name']: o.get('roleInOrg') for o in me.get('orgs', [])}
    how = (f'Fix: an admin of https://huggingface.co/{org} gives account "{me["name"]}" the "write" role, and\n'
           f'HF_TOKEN must allow writes there (fine-grained token: add the {org} org with "Write access to\n'
           f'contents/settings of all repos", or use a classic "write" token). Or set HF_ORG in .env to a\n'
           f'namespace you can write to.')
    if org != me['name'] and org not in orgs:
        raise SystemExit(f'Account "{me["name"]}" is not a member of "{org}".\n{how}')
    from huggingface_hub.errors import HfHubHTTPError
    try:
        api.create_repo(repo, repo_type='dataset', private=private, exist_ok=True)
    except HfHubHTTPError as e:
        if e.response is not None and e.response.status_code in (401, 403):
            raise SystemExit(f'HF refused to create {repo} (HTTP {e.response.status_code}): the token cannot '
                             f'write to "{org}" (org role reported: {orgs.get(org)}).\n{how}')
        raise
    info = api.upload_folder(repo_id=repo, repo_type='dataset', folder_path=release,
                             allow_patterns=[*pinned, 'README.md'],
                             commit_message='Leakage-free Sinhala/Pali/Sanskrit release')
    revision = info.oid
    # Verify the hub copy byte-for-byte before pinning it.
    for name, sha in pinned.items():
        f = api.hf_hub_download(repo, name, repo_type='dataset', revision=revision,
                                local_dir=paths.STATE_DIR / 'publish_check')
        if sha256_file(f) != sha:
            raise SystemExit(f'{name}: uploaded copy differs from the release')
        print(f'[PASS] {name}: hub copy matches sha256')
    locks = json.loads(paths.LOCKS.read_text(encoding='utf-8'))
    templated = repo == hub.target_dataset_repo() and not args.repo
    locks['target_dataset'] = {
        '_comment': locks['target_dataset'].get('_comment', ''),
        'kind': 'dataset',
        'repo_id': '{HF_ORG}/{HF_TARGET_DATASET}' if templated else repo,
        'published_repo': repo, 'revision': revision,
        'probe_file': 'split_report.json', 'files_sha256': pinned}
    paths.LOCKS.write_text(json.dumps(locks, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    vis = 'private' if private else 'public'
    print(f'Published https://huggingface.co/datasets/{repo} ({vis}, revision {revision[:10]}); '
          f'config/locks.json updated.')


if __name__ == '__main__':
    main()
