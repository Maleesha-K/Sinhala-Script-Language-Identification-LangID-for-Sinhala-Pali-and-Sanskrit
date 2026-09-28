"""Human-readable names for fastText LID label codes.

Codes follow the NLLB/FLORES `language_Script` convention. GlotLID v3 carries
2,104 of them, so this covers the common ones and falls back to a readable
rendering of the raw code for the rest.
"""

# Most frequent ISO 639-3 codes across the two label spaces.
LANGUAGE_NAMES = {
    "sin": "Sinhala", "pli": "Pali", "san": "Sanskrit", "tam": "Tamil",
    "hin": "Hindi", "ben": "Bengali", "eng": "English", "fra": "French",
    "deu": "German", "arb": "Arabic", "ara": "Arabic", "ary": "Moroccan Arabic",
    "arz": "Egyptian Arabic", "ars": "Najdi Arabic", "apc": "Levantine Arabic",
    "acm": "Iraqi Arabic", "aeb": "Tunisian Arabic", "urd": "Urdu",
    "npi": "Nepali", "nep": "Nepali", "mar": "Marathi", "guj": "Gujarati",
    "pan": "Punjabi", "tel": "Telugu", "kan": "Kannada", "mal": "Malayalam",
    "ory": "Odia", "asm": "Assamese", "mai": "Maithili", "bho": "Bhojpuri",
    "awa": "Awadhi", "mag": "Magahi", "hne": "Chhattisgarhi", "kas": "Kashmiri",
    "snd": "Sindhi", "div": "Dhivehi", "bod": "Tibetan", "dzo": "Dzongkha",
    "mya": "Burmese", "tha": "Thai", "lao": "Lao", "khm": "Khmer",
    "vie": "Vietnamese", "zho": "Chinese", "cmn": "Chinese", "yue": "Cantonese",
    "jpn": "Japanese", "kor": "Korean", "rus": "Russian", "ukr": "Ukrainian",
    "pol": "Polish", "ces": "Czech", "slk": "Slovak", "bul": "Bulgarian",
    "srp": "Serbian", "hrv": "Croatian", "bos": "Bosnian", "slv": "Slovenian",
    "mkd": "Macedonian", "ell": "Greek", "tur": "Turkish", "aze": "Azerbaijani",
    "kaz": "Kazakh", "kir": "Kyrgyz", "uzb": "Uzbek", "tuk": "Turkmen",
    "tat": "Tatar", "bak": "Bashkir", "chv": "Chuvash", "mon": "Mongolian",
    "fas": "Persian", "pes": "Persian", "prs": "Dari", "pbt": "Pashto",
    "pus": "Pashto", "ckb": "Kurdish", "kmr": "Kurmanji Kurdish",
    "heb": "Hebrew", "amh": "Amharic", "tir": "Tigrinya", "som": "Somali",
    "swh": "Swahili", "swa": "Swahili", "hau": "Hausa", "yor": "Yoruba",
    "ibo": "Igbo", "zul": "Zulu", "xho": "Xhosa", "afr": "Afrikaans",
    "nld": "Dutch", "spa": "Spanish", "por": "Portuguese", "ita": "Italian",
    "ron": "Romanian", "cat": "Catalan", "glg": "Galician", "eus": "Basque",
    "swe": "Swedish", "dan": "Danish", "nor": "Norwegian", "nob": "Norwegian",
    "nno": "Norwegian Nynorsk", "isl": "Icelandic", "fin": "Finnish",
    "est": "Estonian", "lav": "Latvian", "lvs": "Latvian", "lit": "Lithuanian",
    "hun": "Hungarian", "sqi": "Albanian", "als": "Albanian", "hye": "Armenian",
    "kat": "Georgian", "mlt": "Maltese", "gle": "Irish", "cym": "Welsh",
    "ind": "Indonesian", "msa": "Malay", "zsm": "Malay", "jav": "Javanese",
    "sun": "Sundanese", "tgl": "Tagalog", "fil": "Filipino", "ceb": "Cebuano",
    "war": "Waray", "ilo": "Ilocano", "epo": "Esperanto", "lat": "Latin",
}

SCRIPT_NAMES = {
    "Sinh": "Sinhala", "Deva": "Devanagari", "Taml": "Tamil", "Beng": "Bengali",
    "Arab": "Arabic", "Latn": "Latin", "Cyrl": "Cyrillic", "Grek": "Greek",
    "Hebr": "Hebrew", "Thai": "Thai", "Laoo": "Lao", "Mymr": "Myanmar",
    "Khmr": "Khmer", "Tibt": "Tibetan", "Ethi": "Ethiopic", "Geor": "Georgian",
    "Armn": "Armenian", "Hang": "Hangul", "Hani": "Han", "Jpan": "Japanese",
    "Hans": "Simplified Han", "Hant": "Traditional Han", "Guru": "Gurmukhi",
    "Gujr": "Gujarati", "Knda": "Kannada", "Mlym": "Malayalam", "Orya": "Odia",
    "Telu": "Telugu", "Olck": "Ol Chiki", "Tfng": "Tifinagh", "Nkoo": "N'Ko",
}


def describe_code(code: str) -> str:
    """Render 'tam_Taml' as 'Tamil', 'san_Deva' as 'Sanskrit (Devanagari)'.

    The script is only shown when it disambiguates: a language written in
    several scripts in the label space, or an unknown language code.
    """
    if not code:
        return "unknown"
    parts = code.split("_")
    lang = parts[0]
    script = parts[1] if len(parts) > 1 else None
    name = LANGUAGE_NAMES.get(lang)

    if name is None:
        # Unknown language: keep the raw code, but expand the script if we can.
        if script and script in SCRIPT_NAMES:
            return f"{lang} ({SCRIPT_NAMES[script]})"
        return code

    # Sanskrit appears in both Sinhala and Devanagari; always disambiguate it.
    if lang == "san" and script in SCRIPT_NAMES:
        return f"{name} ({SCRIPT_NAMES[script]})"
    return name
