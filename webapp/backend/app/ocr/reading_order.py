"""Reading order for OCR engines that return bare text lines (Surya).

Tesseract does its own layout analysis; Surya returns lines in detection order,
which interleaves the columns of a multi-column page. `lines_to_text` puts the
lines back in reading order and marks paragraphs the way Tesseract does (a
blank line between them):

  * a region with a vertical gutter (whitespace no line crosses, with at least
    two rows on each side, side by side) is read column by column, left to right;
  * a region whose gutter is crossed only by a few wide lines (a centred title,
    a figure caption) is read in bands: the lines above the first such line,
    that line, the lines below it, and so on, each band again by columns;
  * otherwise the region is one column, read top to bottom; lines sharing a row
    (e.g. table cells) are joined left to right.
"""

from dataclasses import dataclass
from statistics import median
from typing import Iterable, List, Optional, Sequence, Tuple

# A gutter must be at least this many median line heights wide.
MIN_GUTTER = 0.5
# At most this share of a region's lines may cross a gutter (titles, captions).
MAX_SPANNING = 1 / 3
# A vertical gap above this many median line heights starts a new paragraph.
PARAGRAPH_GAP = 0.8


@dataclass(frozen=True)
class Line:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str

    @property
    def height(self) -> float:
        return self.y1 - self.y0


def _widest_gap(lines: Sequence[Line], min_width: float) -> Optional[Tuple[float, float]]:
    """Widest interior x-interval no line covers, if at least `min_width` wide."""
    if len(lines) < 2:
        return None
    spans = sorted((l.x0, l.x1) for l in lines)
    best, reach = None, spans[0][1]
    for x0, x1 in spans[1:]:
        if x0 - reach >= min_width and (best is None or x0 - reach > best[1] - best[0]):
            best = (reach, x0)
        reach = max(reach, x1)
    return best


def _rows(lines: Sequence[Line]) -> List[List[Line]]:
    """Lines grouped into rows of vertically overlapping lines, top to bottom."""
    rows: List[List[Line]] = []
    bottom = None
    for line in sorted(lines, key=lambda l: (l.y0, l.x0)):
        overlaps = bottom is not None and line.y0 < bottom - 0.5 * line.height
        if overlaps:
            rows[-1].append(line)
            bottom = max(bottom, line.y1)
        else:
            rows.append([line])
            bottom = line.y1
    return [sorted(row, key=lambda l: l.x0) for row in rows]


def _columns(lines: Sequence[Line], unit: float):
    """(gutter, left, right) when the lines form two side-by-side columns."""
    gutter = _widest_gap(lines, MIN_GUTTER * unit)
    if gutter is None:
        return None
    cut = (gutter[0] + gutter[1]) / 2
    left = [l for l in lines if (l.x0 + l.x1) / 2 < cut]
    right = [l for l in lines if (l.x0 + l.x1) / 2 >= cut]
    # Cells of a single row, or blocks at different heights, are not columns.
    if len(_rows(left)) < 2 or len(_rows(right)) < 2:
        return None
    if min(max(l.y1 for l in left), max(l.y1 for l in right)) <= max(
        min(l.y0 for l in left), min(l.y0 for l in right)
    ):
        return None
    return gutter, left, right


def _blocks(lines: Sequence[Line], unit: float) -> List[List[List[Line]]]:
    """Blocks (columns or bands) in reading order, each a list of rows."""
    if not lines:
        return []
    columns = _columns(lines, unit)
    if columns is not None:
        _, left, right = columns
        return _blocks(left, unit) + _blocks(right, unit)

    # Wide lines may hide a gutter: set the widest aside until one shows, then
    # read in bands around the lines that cross it.
    by_width = sorted(lines, key=lambda l: l.x1 - l.x0)
    for k in range(1, int(len(lines) * MAX_SPANNING) + 1):
        columns = _columns(by_width[:-k], unit)
        if columns is None:
            continue
        gutter = columns[0]
        crosses = lambda l: l.x0 < gutter[0] and l.x1 > gutter[1]
        spanning = sorted((l for l in lines if crosses(l)), key=lambda l: l.y0)
        if not spanning:
            continue
        others = [l for l in lines if not crosses(l)]
        blocks: List[List[List[Line]]] = []
        top = float("-inf")
        for span in spanning + [None]:
            bottom = span.y0 if span is not None else float("inf")
            band = [l for l in others if top <= (l.y0 + l.y1) / 2 < bottom]
            blocks += _blocks(band, unit)
            if span is not None:
                blocks.append([[span]])
                top = span.y1
        return blocks

    return [_rows(lines)]


def lines_to_text(lines: Iterable[Line]) -> str:
    """The lines' text in reading order, paragraphs separated by a blank line."""
    lines = [l for l in lines if l.text.strip()]
    if not lines:
        return ""
    unit = median(l.height for l in lines)
    paragraphs: List[List[str]] = []
    for block in _blocks(lines, unit):
        paragraphs.append([])
        previous = None
        for row in block:
            if previous is not None and row[0].y0 - previous > PARAGRAPH_GAP * unit:
                paragraphs.append([])
            paragraphs[-1].append(" ".join(l.text.strip() for l in row))
            previous = max(l.y1 for l in row)
    return "\n\n".join("\n".join(p) for p in paragraphs if p)
