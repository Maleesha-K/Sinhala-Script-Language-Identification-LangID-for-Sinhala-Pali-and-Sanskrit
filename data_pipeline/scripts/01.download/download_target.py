"""Target-language dataset (Sinhala / Pali / Sanskrit in Sinhala script).

Fetched from the pinned Hugging Face release, or from the maintainer's local
release before publication. Either way every file must match the sha256 pinned
in config/locks.json, so all researchers evaluate on byte-identical splits.
"""
import shutil
from pathlib import Path

from lidpipe import config, paths
from lidpipe.download import hf_snapshot
from lidpipe.manifest import prepare_output, reset_dir, sha256_file, write_manifest

lock = config.locks()['target_dataset']
want = lock['files_sha256']
out = reset_dir(paths.TARGET)

if lock['kind'] == 'dataset':
    staging = paths.TARGET / '_download'
    hf_snapshot('target_dataset', staging, list(want))
    source = staging
elif lock['kind'] == 'local_release':
    source = paths.ROOT / lock['path']
else:
    raise SystemExit(f'unsupported target_dataset kind {lock["kind"]!r}')

files = []
for name, sha in want.items():
    src = Path(source) / name
    if not src.exists():
        raise SystemExit(f'{src} missing')
    if sha256_file(src) != sha:
        raise SystemExit(f'{name}: sha256 differs from config/locks.json; this is not the pinned release')
    split = name.removesuffix('.jsonl')
    dst = prepare_output(out / split / name if name.endswith('.jsonl') else out / name)
    shutil.copyfile(src, dst)
    files.append(dst)
shutil.rmtree(paths.TARGET / '_download', ignore_errors=True)
write_manifest(out, '01.download', files, extra={'source': {'target_dataset': lock}})
print(f'target dataset ({lock["kind"]}) -> {out}: ' + ', '.join(f.name for f in files))
