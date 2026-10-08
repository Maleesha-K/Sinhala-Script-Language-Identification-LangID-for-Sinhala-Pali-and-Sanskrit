"""ConLID (EPFL) through lidlab's independent re-implementation of the released
inference architecture (new_method/lidlab/backends.py), verified there against
the official checkpoint."""
import sys
from pathlib import Path

from .. import paths

sys.path.insert(0, str(paths.ROOT / 'new_method'))
from lidlab.backends import ConLIDBackend  # noqa: E402

from ..device import torch_device  # noqa: E402


class ConLID:
    def __init__(self, path):
        self.path = Path(path)
        self.backend = ConLIDBackend(self.path, torch_device())
        self.labels = list(self.backend.labels)

    def predict(self, texts, batch_size=256):
        out_labels, conf = [], []
        texts = list(texts)
        for start in range(0, len(texts), batch_size):
            chunk = texts[start:start + batch_size]
            try:
                l, c = self.backend.predict(chunk, None, batch_size)
            except ValueError:  # a text without ConLID features: predict per row
                l, c = [], []
                for t in chunk:
                    try:
                        a, b = self.backend.predict([t], None, 1)
                    except ValueError:
                        a, b = ['__none__'], [0.0]  # abstains; scored as wrong
                    l += a
                    c += b
            out_labels += l
            conf += c
        return out_labels, conf
