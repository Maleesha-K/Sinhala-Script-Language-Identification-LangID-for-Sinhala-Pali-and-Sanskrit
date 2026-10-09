"""fastText models (LID-176, OpenLID-v3, GlotLID-v3, NLLB-218) through the
bundled fastText v0.9.2 executable (new_method/native). It predicts with the
official C++ code path for both softmax and hierarchical-softmax models, and
continues training softmax models with every original label kept in place.
"""
import importlib.util
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

from .. import paths

NATIVE_ROOT = paths.ROOT / 'new_method'


@lru_cache(maxsize=None)
def executable():
    spec = importlib.util.spec_from_file_location('build_native', NATIVE_ROOT / 'scripts' / 'build_native.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return Path(module.build(NATIVE_ROOT))


class NativeModel:
    def __init__(self, path):
        self.path = Path(path)
        out = subprocess.check_output([str(executable()), 'inspect', str(self.path)], text=True)
        self.metadata, self.labels = {}, []
        for row in out.splitlines():
            key, value = row.split('\t', 1)
            if key == 'label':
                self.labels.append(value.removeprefix('__label__'))
            else:
                self.metadata[key] = value
        self.loss = self.metadata['loss']

    def predict(self, texts):
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp) / 'in.txt', Path(tmp) / 'out.tsv'
            # Inputs are already normalised single-line text; fastText needs no newlines.
            src.write_text(''.join(t.replace('\n', ' ') + '\n' for t in texts), encoding='utf-8')
            subprocess.run([str(executable()), 'predict', str(self.path), str(src), str(dst)], check=True)
            rows = [line.split('\t') for line in dst.read_text(encoding='utf-8').splitlines()]
        if len(rows) != len(texts):
            raise RuntimeError(f'{len(rows)} predictions for {len(texts)} texts')
        return [r[0].removeprefix('__label__') for r in rows], [float(r[1]) for r in rows]

    def continue_training(self, rows, out_path, lr, seed, add_labels=()):
        """One pass over `rows` (dicts with text/label) from this checkpoint,
        linear lr decay within the pass; returns the new model."""
        if self.loss != 'softmax':
            raise ValueError(f'{self.path.name}: continued training needs a softmax model, got {self.loss}')
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            data, labels = Path(tmp) / 'train.txt', Path(tmp) / 'labels.txt'
            data.write_text(''.join(f'__label__{r["label"]} {r["text"]}\n' for r in rows), encoding='utf-8')
            wanted = sorted({r['label'] for r in rows} | set(add_labels))
            labels.write_text(''.join(f'__label__{l}\n' for l in wanted), encoding='utf-8')
            subprocess.run([str(executable()), 'train', str(self.path), str(data), str(labels), str(out_path),
                            str(lr), str(len(rows) if rows else 0), str(seed)], check=True)
        model = NativeModel(out_path)
        if model.labels[:len(self.labels)] != self.labels:
            raise AssertionError('original labels were reordered or removed')
        return model
