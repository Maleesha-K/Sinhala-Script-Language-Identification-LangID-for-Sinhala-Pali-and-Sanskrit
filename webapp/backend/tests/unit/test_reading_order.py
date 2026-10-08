"""Reading order for line-level OCR output (app/ocr/reading_order.py)."""
from app.ocr.reading_order import Line, lines_to_text

H = 20  # line height
STEP = 28  # baseline-to-baseline distance within a paragraph


def column(x0, x1, y, paragraphs, prefix):
    """Lines of a column: `paragraphs` line counts, one line-height gap between them."""
    out = []
    for p, count in enumerate(paragraphs, 1):
        for n in range(1, count + 1):
            out.append(Line(x0, y, x1, y + H, f"{prefix}{p}.{n}"))
            y += STEP
        y += H
    return out


def test_two_columns_under_a_centred_title_are_read_column_by_column():
    title = Line(150, 0, 450, 30, "Title")
    left = column(0, 280, 60, [3, 2], "L")
    right = column(320, 600, 60, [3, 2], "R")
    # Detection order interleaves the rows of the two columns.
    lines = [title] + [l for pair in zip(left, right) for l in pair]

    assert lines_to_text(lines) == (
        "Title\n\n"
        "L1.1\nL1.2\nL1.3\n\nL2.1\nL2.2\n\n"
        "R1.1\nR1.2\nR1.3\n\nR2.1\nR2.2"
    )


def test_a_left_aligned_title_is_read_before_the_columns():
    title = Line(0, 0, 200, 30, "Title")
    lines = [title] + column(0, 280, 60, [2], "L") + column(320, 600, 60, [2], "R")

    assert lines_to_text(reversed(lines)) == "Title\n\nL1.1\nL1.2\n\nR1.1\nR1.2"


def test_a_full_width_caption_between_two_column_sections_separates_them():
    top = column(0, 280, 0, [2], "A") + column(320, 600, 0, [2], "B")
    caption = Line(0, 100, 600, 120, "Fig. 1 caption across the page")
    bottom = column(0, 280, 150, [2], "C") + column(320, 600, 150, [2], "D")

    assert lines_to_text(bottom + [caption] + top) == (
        "A1.1\nA1.2\n\nB1.1\nB1.2\n\n"
        "Fig. 1 caption across the page\n\n"
        "C1.1\nC1.2\n\nD1.1\nD1.2"
    )


def test_single_column_keeps_line_breaks_and_marks_paragraphs():
    lines = column(0, 500, 0, [2, 1, 3], "P")
    # A shorter, indented line does not make the page two columns.
    lines[1] = Line(40, lines[1].y0, 300, lines[1].y1, "P1.2")

    assert lines_to_text(lines[::-1]) == "P1.1\nP1.2\n\nP2.1\n\nP3.1\nP3.2\nP3.3"


def test_cells_on_one_row_are_joined_left_to_right():
    lines = [
        Line(300, 0, 400, 20, "value"),
        Line(0, 2, 100, 22, "name"),
        Line(0, 30, 400, 50, "next line spanning the row"),
    ]

    assert lines_to_text(lines) == "name value\nnext line spanning the row"


def test_blank_and_empty_input():
    assert lines_to_text([]) == ""
    assert lines_to_text([Line(0, 0, 10, 10, "  ")]) == ""
