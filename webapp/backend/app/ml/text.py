"""Input normalisation for the fine-tuned models.

Port of data_pipeline/lidpipe/text.py `normalise`, which every training and
evaluation input went through. Keep it identical.
"""

import re
import unicodedata

# Invisible characters that carry no linguistic content. ZWJ (U+200D) and ZWNJ
# (U+200C) are deliberately kept: Sinhala uses ZWJ for yansaya/rakaransaya and
# conjuncts, and Devanagari/Bengali use both for conjunct control.
_DROP = dict.fromkeys(map(ord, "\x00﻿​⁠"), " ")
_SPACE = re.compile(r"\s+")


def normalise(text: str) -> str:
    """NFC + invisible-character removal + whitespace collapse. Idempotent."""
    text = unicodedata.normalize("NFC", str(text).translate(_DROP))
    return _SPACE.sub(" ", text).strip()
