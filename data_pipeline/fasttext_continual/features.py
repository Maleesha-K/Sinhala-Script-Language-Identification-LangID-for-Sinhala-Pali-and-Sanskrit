"""Feature IDs compatible with the unpruned, wordNgrams=1 LID-176 model.

No Unicode normalization, lowercasing, vocabulary rebuilding or deduplication
of feature IDs: repetitions contribute to fastText's feature mean.
"""

import re
from functools import lru_cache

ASCII_SEPARATORS = re.compile(r"[ \t\r\v\f\x00]+")
EOS = "</s>"


def single_line(text):
    """Explicit common preprocessing for JSONL records and native comparisons."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return text.replace("\n", " ")


def tokens(text):
    # fastText.predict appends a newline, which creates an EOS token. The
    # literal EOS also terminates a line. Non-ASCII whitespace is NOT split.
    if "\n" in text:
        raise ValueError("Call single_line() before tokenization")
    for token in ASCII_SEPARATORS.split(text):
        if not token:
            continue
        yield token
        if token == EOS:
            return
    yield EOS


def fasttext_hash(data):
    """FNV-1a with fastText's historical SIGNED UTF-8 bytes."""
    h = 2166136261
    for byte in data:
        signed = byte if byte < 128 else byte - 256
        h = ((h ^ (signed & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return h


class FeatureEncoder:
    def __init__(self, words, args):
        if args["wordNgrams"] != 1:
            raise ValueError("This importer supports wordNgrams=1 only")
        self.words = list(words)
        self.word_to_id = {word: i for i, word in enumerate(words)}
        self.args = dict(args)
        self.nwords = len(words)
        if EOS not in self.word_to_id:
            raise ValueError("Expected an EOS word in the original vocabulary")
        # Bounded cache, per encoder instance; never stores hidden vectors.
        self.word_ids = lru_cache(maxsize=32768)(self._word_ids)

    def _word_ids(self, word):
        if word.startswith(self.args["label"]):
            return ()
        ids = []
        wid = self.word_to_id.get(word)
        if wid is not None:
            ids.append(wid)
        if word == EOS or self.args["maxn"] <= 0:
            return tuple(ids)
        # Python slices count Unicode codepoints; C++ skips UTF-8 continuation
        # bytes to count the same units (including combining marks separately).
        wrapped = "<" + word + ">"
        for i in range(len(wrapped)):
            for n in range(1, self.args["maxn"] + 1):
                j = i + n
                if j > len(wrapped):
                    break
                if n < self.args["minn"]:
                    continue
                if n == 1 and (i == 0 or j == len(wrapped)):
                    continue
                h = fasttext_hash(wrapped[i:j].encode("utf-8"))
                ids.append(self.nwords + h % self.args["bucket"])
        return tuple(ids)

    def encode(self, text):
        ids = []
        for word in tokens(single_line(text)):
            ids.extend(self.word_ids(word))
        if not ids:
            raise ValueError("No features; an unmodified LID-176 EOS was expected")
        return ids
