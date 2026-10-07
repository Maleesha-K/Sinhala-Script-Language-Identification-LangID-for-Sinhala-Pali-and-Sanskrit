"""Text normalisation and script detection, used for every dataset and model input."""
import hashlib
import re
import unicodedata
from collections import Counter

# Invisible characters that carry no linguistic content. ZWJ (U+200D) and ZWNJ
# (U+200C) are deliberately kept: Sinhala uses ZWJ for yansaya/rakaransaya and
# conjuncts, and Devanagari/Bengali use both for conjunct control.
_DROP = dict.fromkeys(map(ord, '\x00﻿​⁠'), ' ')
_SPACE = re.compile(r'\s+')


def normalise(text):
    """NFC + invisible-character removal + whitespace collapse. Idempotent."""
    text = unicodedata.normalize('NFC', str(text).translate(_DROP))
    return _SPACE.sub(' ', text).strip()


def is_normalised(text):
    return text == normalise(text)


def text_sha256(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


# First word of the Unicode character name -> ISO 15924 code.
_SCRIPT_BY_NAME = {
    'LATIN': 'Latn', 'SINHALA': 'Sinh', 'DEVANAGARI': 'Deva', 'ARABIC': 'Arab',
    'TAMIL': 'Taml', 'BENGALI': 'Beng', 'CYRILLIC': 'Cyrl', 'GREEK': 'Grek',
    'HEBREW': 'Hebr', 'CJK': 'Hani', 'HIRAGANA': 'Jpan', 'KATAKANA': 'Jpan',
    'HANGUL': 'Kore', 'THAI': 'Thai', 'GEORGIAN': 'Geor', 'ARMENIAN': 'Armn',
    'ETHIOPIC': 'Ethi', 'GUJARATI': 'Gujr', 'GURMUKHI': 'Guru', 'KANNADA': 'Knda',
    'MALAYALAM': 'Mlym', 'TELUGU': 'Telu', 'ORIYA': 'Orya', 'TIBETAN': 'Tibt',
    'MYANMAR': 'Mymr', 'KHMER': 'Khmr', 'LAO': 'Laoo', 'MONGOLIAN': 'Mong',
    'TIFINAGH': 'Tfng', 'THAANA': 'Thaa', 'SYRIAC': 'Syrc', 'CHEROKEE': 'Cher',
    'NKO': 'Nkoo', 'OL': 'Olck', 'CANADIAN': 'Cans', 'BALINESE': 'Bali',
    'JAVANESE': 'Java', 'SUNDANESE': 'Sund', 'CHAKMA': 'Cakm', 'MEETEI': 'Mtei',
    'ADLAM': 'Adlm', 'VAI': 'Vaii', 'BOPOMOFO': 'Bopo', 'YI': 'Yiii',
}


def script_counts(text):
    """Count letters and combining marks per ISO 15924 script."""
    counts = Counter()
    for ch in text:
        if unicodedata.category(ch)[0] not in 'LM':
            continue
        try:
            word = unicodedata.name(ch).split()[0]
        except ValueError:
            continue
        code = _SCRIPT_BY_NAME.get(word)
        if code:
            counts[code] += 1
    # Japanese text mixes kana with Han; any kana makes the whole text Jpan.
    if counts['Jpan'] and counts['Hani']:
        counts['Jpan'] += counts.pop('Hani')
    return counts


def script_of(text):
    """Majority ISO 15924 script of the letters in `text`, or 'Zyyy' if none."""
    counts = script_counts(text)
    return counts.most_common(1)[0][0] if counts else 'Zyyy'


def letter_count(text):
    return sum(script_counts(text).values())


# Sentence terminators: Latin . ? !, Devanagari danda/double danda, Sinhala
# kunddaliya (U+0DF4). A split needs following whitespace, so decimals and
# abbreviations without a space stay intact.
_SENTENCE_END = re.compile(r'(?<=[.?!।॥෴])\s+')


def _hard_wrap(sentence, max_chars):
    words, cur = sentence.split(' '), ''
    for w in words:
        while len(w) > max_chars:  # a single "word" longer than the limit
            if cur:
                yield cur
                cur = ''
            yield w[:max_chars]
            w = w[max_chars:]
        if cur and len(cur) + 1 + len(w) > max_chars:
            yield cur
            cur = w
        else:
            cur = f'{cur} {w}' if cur else w
    if cur:
        yield cur


def segment(text, max_chars):
    """Split normalised text into sentence-level units of at most `max_chars`.

    Sentences are packed greedily in order; a sentence longer than the limit is
    wrapped at spaces. Text already within the limit is returned unchanged.
    """
    if len(text) <= max_chars:
        return [text]
    units, cur = [], ''
    for sentence in _SENTENCE_END.split(text):
        for piece in ([sentence] if len(sentence) <= max_chars else _hard_wrap(sentence, max_chars)):
            if cur and len(cur) + 1 + len(piece) > max_chars:
                units.append(cur)
                cur = piece
            else:
                cur = f'{cur} {piece}' if cur else piece
    if cur:
        units.append(cur)
    return units
