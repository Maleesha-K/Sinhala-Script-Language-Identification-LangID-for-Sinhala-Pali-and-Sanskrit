"""Short-text stress test: k-word fragments of the target test split.

Same method as the original phase-1 study (scripts/benchmark_phase1_baselines.py):
from each test sentence take k contiguous words starting at a random word;
sentences with <= k words are kept whole. Differences, both for
reproducibility: words are whitespace tokens with at least one letter (a
fragment is never bare punctuation), and each row's start is drawn from its own
generator seeded by (seed, k, sample_id), so a fragment does not depend on file
order.
"""
import hashlib

import numpy as np

from . import config, paths
from .text import letter_count


def words_of(text):
    return [w for w in text.split() if letter_count(w)]


def fragment(text, k, seed, sample_id):
    words = words_of(text)
    if len(words) <= k:
        return ' '.join(words)
    key = int.from_bytes(hashlib.sha256(f'{sample_id}'.encode()).digest()[:8], 'little')
    start = int(np.random.default_rng([seed, k, key]).integers(0, len(words) - k + 1))
    return ' '.join(words[start:start + k])


def sizes():
    return list(config.pipeline()['fragments']['words'])


def name(k):
    return f'target_test_{k}w'


def path(k):
    return paths.FRAGMENTS / f'{name(k)}.jsonl'
