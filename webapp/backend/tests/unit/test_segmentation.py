"""Segmentation strategies (classification_tasks.split_segments)."""
from app.workers.tasks.classification_tasks import split_segments


def texts(text, strategy):
    segments = split_segments(text, strategy)
    # Offsets always point back into the text.
    assert all(text[s["start"]:s["end"]] == s["text"] for s in segments)
    return [s["text"].strip() for s in segments]


def test_document_joins_printed_line_wraps_into_one_sentence():
    page = "This edition brings together\nverses from the Dhammapada,\nthe Bhagavad Gita and the\nKaraniya Metta Sutta. Each is\nfollowed by a discussion."
    assert texts(page, "document") == [
        "This edition brings together\nverses from the Dhammapada,\nthe Bhagavad Gita and the\nKaraniya Metta Sutta.",
        "Each is\nfollowed by a discussion.",
    ]
    # The sentence strategy (pasted text) still breaks at every line.
    assert len(texts(page, "sentence")) == 6


def test_document_keeps_paragraphs_verses_and_introduced_quotes_apart():
    page = (
        "ධම්මපදය ප්‍රසිද්ධ ග්‍රන්ථයකි. එහි පළමු ගාථාව මෙසේය:\n"
        "මනොපුබ්බඞ්ගමා ධම්මා මනොසෙට්ඨා මනොමයා.\n"
        "මනසා චෙ පදුට්ඨෙන භාසති වා කරොති වා.\n"
        "\n"
        "A heading without punctuation\n"
        "\n"
        "Next paragraph"
    )
    assert texts(page, "document") == [
        "ධම්මපදය ප්‍රසිද්ධ ග්‍රන්ථයකි.",
        "එහි පළමු ගාථාව මෙසේය:",
        "මනොපුබ්බඞ්ගමා ධම්මා මනොසෙට්ඨා මනොමයා.",
        "මනසා චෙ පදුට්ඨෙන භාසති වා කරොති වා.",
        "A heading without punctuation",
        "Next paragraph",
    ]


def test_document_does_not_split_inside_numbers_or_abbreviations():
    assert texts("Version 3.14 of the text, ක්‍රි.පූ. 5 වන සියවස.", "document") == [
        "Version 3.14 of the text, ක්‍රි.පූ.",
        "5 වන සියවස.",
    ]


def test_document_handles_empty_and_blank_text():
    assert split_segments("", "document") == []
    assert split_segments("\n\n  \n", "document") == []
