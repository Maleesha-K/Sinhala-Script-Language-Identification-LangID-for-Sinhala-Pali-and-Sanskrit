"""Label space and the one mapping applied to gold labels and predictions."""
from . import config
from .text import script_of

_L = config.labels()
TARGET = list(_L['target'])
REPLAY = list(_L['replay'])
SCORED = TARGET + REPLAY
EXPECTED_SCRIPT = dict(_L['expected_script'])
MULTI_SCRIPT = {k: set(v) for k, v in _L['multi_script'].items()}
ABSENT_BY_DESIGN = {k: set(v) for k, v in _L['absent_by_design'].items()}
_GOLD_OVERRIDES = _L['gold_overrides']
_PRED_ALIASES = _L['prediction_language_aliases']


def gold_language(benchmark, raw_code):
    """Raw benchmark language code -> ISO 639-3 (no macrolanguage merging)."""
    raw_code = str(raw_code).strip()
    return (_GOLD_OVERRIDES.get(benchmark) or {}).get(raw_code, raw_code)


def canonical_prediction(raw, text):
    """Model output -> `<lang>_<Script>`.

    Strips `__label__`, maps 2-letter/long-form codes through
    `prediction_language_aliases`, and takes the script from the input text when
    the model emits none. Unknown codes pass through unchanged; they are simply
    outside the scored label set.
    """
    raw = str(raw).removeprefix('__label__').strip()
    lang, _, script = raw.partition('_')
    lang = _PRED_ALIASES.get(lang, lang)
    return f'{lang}_{script or script_of(text)}'
