import pytest
from app.workers.tasks.classification_tasks import _segment_text

def test_segment_text_empty_and_none():
    """Verify that empty, None, or whitespace-only inputs return empty list."""
    assert _segment_text("", "sentence") == []
    assert _segment_text(None, "sentence") == []
    assert _segment_text("   \n\t  ", "sentence") == []

def test_segment_text_full_text_strategy():
    """Verify full_text strategy returns the exact input string as a single segment."""
    text = "මෙය සම්පූර්ණ ලියවිල්ලකි. මෙය වාක්‍ය කිහිපයකින් සමන්විත වේ."
    segments = _segment_text(text, "full_text")
    
    assert len(segments) == 1
    assert segments[0]["text"] == text
    assert segments[0]["start"] == 0
    assert segments[0]["end"] == len(text)

def test_segment_text_paragraph_strategy():
    """Verify paragraph strategy correctly splits by newlines."""
    text = "පළමු ඡේදය මෙසේය.\n\nදෙවන ඡේදය මෙසේ ආරම්භ වේ.\nතෙවන පේළිය."
    segments = _segment_text(text, "paragraph")
    
    assert len(segments) >= 2
    for seg in segments:
        assert seg["text"].strip() != ""
        assert seg["start"] < seg["end"]
        assert text[seg["start"]:seg["end"]] == seg["text"]

def test_segment_text_sentence_latin_punctuation():
    """Verify sentence strategy correctly splits on periods, exclamation marks, question marks."""
    text = "පළමු වාක්‍යයයි. දෙවන වාක්‍යයද? තුන්වන වාක්‍යයයි!"
    segments = _segment_text(text, "sentence")
    
    assert len(segments) == 3
    assert "පළමු වාක්‍යයයි" in segments[0]["text"]
    assert "දෙවන වාක්‍යයද" in segments[1]["text"]
    assert "තුන්වන වාක්‍යයයි" in segments[2]["text"]

def test_segment_text_sentence_indic_danda():
    """Verify sentence strategy splits on the Indic danda (।) character used in Pali and Sanskrit."""
    text = "නමෝ තස්ස භගවතෝ। අරහතෝ සම්මාසම්බුද්ධස්ස। ඒවං මේ සුතං।"
    segments = _segment_text(text, "sentence")
    
    assert len(segments) == 3
    assert "නමෝ තස්ස භගවතෝ" in segments[0]["text"]
    assert "අරහතෝ සම්මාසම්බුද්ධස්ස" in segments[1]["text"]
    assert "ඒවං මේ සුතං" in segments[2]["text"]

def test_segment_text_auto_strategy():
    """Verify auto strategy aggressively splits on clauses, punctuation, and parentheses."""
    text = "සංස්කෘත (දේවභාෂා), පාලි [මාගධී]; සිංහල භාෂාව."
    segments = _segment_text(text, "auto")
    
    assert len(segments) >= 3
    for seg in segments:
        assert seg["text"].strip() != ""
        assert seg["start"] < seg["end"]

def test_segment_text_fallback_for_unknown_strategy():
    """Verify unknown strategy gracefully falls back to full_text."""
    text = "ඕනෑම පෙළක්."
    segments = _segment_text(text, "unsupported_strategy_xyz")
    assert len(segments) == 1
    assert segments[0]["text"] == text
