"""Create the WiLI-2018 Hindi-Deva radar pilot from the latest results CSV."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = REPO_ROOT / "Comparison Tables - Sheet1 (3).csv"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "Overleaf" / "figures"
OUTPUT_STEM = "radar_pilot_wili2018_hindi_deva"
TARGET_LANGUAGE = "Hindi-Deva"
MODEL_NAMES = (
    ("XLM-R Base", "XLM-R Base"),
    ("ConLID", "ConLID"),
    ("fastText LID-176", "fastText LID-176"),
    ("GlotLID v3", "GlotLID v3"),
    ("NLLB LID-218", "NLLB LID-218"),
    ("OpenLID-v2", "OpenLID-v3"),  # Correct the CSV's model-version label.
)
PLOT_LABELS = ("XLM-R", "ConLID", "fastText-176", "GlotLID v3", "NLLB-218", "OpenLID-v3")


def read_fine_tuning_scores(csv_path: Path) -> list[float]:
    with csv_path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.reader(stream))

    section_rows = [
        index
        for index, row in enumerate(rows)
        if any(cell.strip().lower() == "finetuning results" for cell in row)
    ]
    if len(section_rows) != 1:
        raise ValueError("Expected one FineTuning Results section")
    section_index = section_rows[0]

    header_index = next(
        (
            index
            for index in range(section_index + 1, len(rows))
            if sum(cell.strip().lower() == "model" for cell in rows[index]) == 3
        ),
        None,
    )
    if header_index is None:
        raise ValueError("Could not find the three benchmark header blocks")
    header = rows[header_index]
    model_columns = [
        index for index, cell in enumerate(header) if cell.strip().lower() == "model"
    ]
    wili_model_column = model_columns[2]

    benchmark_labels = [
        cell.strip().lower()
        for row in rows[section_index + 1 : header_index]
        for cell in row[wili_model_column:]
    ]
    if "wili-2018" not in benchmark_labels:
        raise ValueError("The third fine-tuning block is not labeled WiLI-2018")

    language_columns = [
        index
        for index in range(wili_model_column + 1, len(header))
        if header[index].strip() == TARGET_LANGUAGE
    ]
    if len(language_columns) != 1:
        raise ValueError(f"Expected one {TARGET_LANGUAGE} column in WiLI-2018")
    score_column = language_columns[0]

    by_model: dict[str, float] = {}
    for row in rows[header_index + 1 :]:
        raw_model = row[wili_model_column].strip() if len(row) > wili_model_column else ""
        if not raw_model:
            if by_model:
                break
            continue
        if raw_model not in dict(MODEL_NAMES):
            raise ValueError(f"Unexpected model in WiLI-2018: {raw_model}")
        if raw_model in by_model:
            raise ValueError(f"Duplicate WiLI-2018 result for {raw_model}")
        if len(row) <= score_column or not row[score_column].strip():
            raise ValueError(f"Missing {TARGET_LANGUAGE} F1 for {raw_model}")
        score = float(row[score_column])
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError(f"Invalid F1 for {raw_model}: {score}")
        by_model[raw_model] = score

    expected = {raw_name for raw_name, _ in MODEL_NAMES}
    if set(by_model) != expected:
        raise ValueError(f"Missing models: {sorted(expected - set(by_model))}")
    return [by_model[raw_name] for raw_name, _ in MODEL_NAMES]


def draw_radar(scores: list[float]) -> plt.Figure:
    labels = PLOT_LABELS
    angles = [2 * math.pi * index / len(labels) for index in range(len(labels))]

    plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42})
    figure, axis = plt.subplots(figsize=(4.6, 4.3), subplot_kw={"projection": "polar"})
    figure.patch.set_facecolor("white")
    axis.set_theta_offset(math.pi / 2)
    axis.set_theta_direction(-1)
    axis.set_ylim(0, 1)
    axis.set_xticks(angles, labels=labels)
    axis.tick_params(axis="x", labelsize=9, pad=14)
    for index, label in enumerate(axis.get_xticklabels()):
        label.set_horizontalalignment(
            "center" if index in (0, 3) else "left" if index in (1, 2) else "right"
        )
    axis.set_yticks([0.25, 0.50, 0.75, 1.00], labels=["0.25", "0.50", "0.75", "1.00"])
    axis.set_rlabel_position(26)
    axis.tick_params(axis="y", labelsize=7, colors="#5B6573")
    axis.grid(color="#CDD5DF", linewidth=0.7)
    axis.spines["polar"].set_color("#4B5563")
    axis.spines["polar"].set_linewidth(0.8)

    axis.plot(
        angles + angles[:1],
        scores + scores[:1],
        color="#0072B2",
        linewidth=1.9,
        marker="o",
        markersize=4.5,
        markerfacecolor="white",
        markeredgewidth=1.5,
        zorder=3,
    )
    figure.suptitle("WiLI-2018  |  Hindi-Deva", fontsize=12, fontweight="semibold", y=0.985)
    figure.text(0.5, 0.925, "Fine-tuned per-language F1", ha="center", fontsize=9, color="#4B5563")
    figure.subplots_adjust(left=0.18, right=0.82, bottom=0.09, top=0.87)
    return figure


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    scores = read_fine_tuning_scores(args.csv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    figure = draw_radar(scores)
    pdf_path = args.output_dir / f"{OUTPUT_STEM}.pdf"
    png_path = args.output_dir / f"{OUTPUT_STEM}.png"
    figure.savefig(
        pdf_path,
        bbox_inches="tight",
        pad_inches=0.15,
        metadata={"Title": "WiLI-2018 Hindi-Deva fine-tuning F1 radar pilot"},
    )
    figure.savefig(png_path, dpi=300, bbox_inches="tight", pad_inches=0.15)
    plt.close(figure)

    for (_, display_name), score in zip(MODEL_NAMES, scores, strict=True):
        print(f"{display_name}: {score:.4f}")
    print(f"PDF: {pdf_path}")
    print(f"PNG: {png_path}")


if __name__ == "__main__":
    main()
