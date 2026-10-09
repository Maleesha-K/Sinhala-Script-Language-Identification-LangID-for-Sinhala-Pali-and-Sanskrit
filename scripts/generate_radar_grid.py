"""Render three-regime, 3 x 11 per-language F1 radar grids from the results CSV."""

from __future__ import annotations

import argparse
import csv
import math
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = REPO_ROOT / "Comparison Tables - New Method (2).csv"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "Overleaf" / "figures"

BENCHMARKS = (
    ("flores_plus", "FLORES+"),
    ("commonlid", "CommonLID"),
    ("wili-2018", "WiLI-2018"),
)
LANGUAGES = (
    "Sinhala-Sinh",
    "Pali-Sinh",
    "Sanskrit-Sinh",
    "Sanskrit-Deva",
    "English-Latn",
    "Tamil-Taml",
    "Hindi-Deva",
    "Bengali-Beng",
    "Arabic-Arab",
    "French-Latn",
    "German-Latn",
)
MODELS = (
    "XLM-R Base",
    "ConLID",
    "fastText LID-176",
    "GlotLID v3",
    "NLLB LID-218",
    "OpenLID-v3",
)
SPOKE_CODES = ("XR", "CL", "FT", "GL", "NL", "OL")
ANGLES = [2 * math.pi * index / len(MODELS) for index in range(len(MODELS))]
REGIMES = (
    ("zero shot results", "Zero-shot", "#0072B2", "-", "o"),
    ("finetune using 3 languages", "Target-only", "#D55E00", "--", "s"),
    ("finetune using all languages", "All-language rehearsal", "#009E73", "-.", "^"),
)
SHOWCASE_LANGUAGES = ("Sinhala-Sinh", "Pali-Sinh", "Sanskrit-Sinh", "English-Latn")
Results = dict[str, dict[str, dict[str, list[float | None]]]]


def normalized_language(label: str) -> str:
    label = label.strip()
    if label.startswith("Arabic-Arab"):
        return "Arabic-Arab"
    return label


def read_results(csv_path: Path) -> Results:
    with csv_path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.reader(stream))

    sections: list[int] = []
    for prefix, name, *_ in REGIMES:
        matches = [
            index for index, row in enumerate(rows)
            if any(cell.strip().lower().startswith(prefix) for cell in row)
        ]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one {name} section; found {len(matches)}")
        sections.append(matches[0])
    if sections != sorted(sections):
        raise ValueError("Result sections are not in the expected order")

    results: Results = {}
    for regime_index, (_, regime_name, *_) in enumerate(REGIMES):
        section_start = sections[regime_index]
        section_end = sections[regime_index + 1] if regime_index + 1 < len(sections) else len(rows)
        headers = [
            index for index in range(section_start + 1, section_end)
            if sum(cell.strip().lower() == "model" for cell in rows[index]) == len(BENCHMARKS)
        ]
        if len(headers) != 1:
            raise ValueError(f"Expected three benchmark headers in {regime_name}")
        header_index = headers[0]
        header = rows[header_index]
        model_columns = [
            index for index, cell in enumerate(header) if cell.strip().lower() == "model"
        ]
        if header_index + len(MODELS) >= section_end:
            raise ValueError(f"Incomplete model rows in {regime_name}")

        results[regime_name] = {}
        for block_index, (raw_benchmark, benchmark) in enumerate(BENCHMARKS):
            model_column = model_columns[block_index]
            block_end = (
                model_columns[block_index + 1]
                if block_index + 1 < len(model_columns) else len(header)
            )
            labels_above = [
                cell.strip().lower()
                for row in rows[section_start + 1 : header_index]
                for cell in row[model_column:block_end]
            ]
            if raw_benchmark not in labels_above:
                raise ValueError(f"Benchmark block {block_index + 1} of {regime_name} is not {benchmark}")

            language_columns = list(range(model_column + 1, model_column + 1 + len(LANGUAGES)))
            actual_languages = tuple(
                normalized_language(header[index]) for index in language_columns
            )
            if actual_languages != LANGUAGES:
                raise ValueError(
                    f"Unexpected language order in {regime_name}/{benchmark}: {actual_languages}"
                )

            by_model: dict[str, list[float | None]] = {}
            for row in rows[header_index + 1 : header_index + 1 + len(MODELS)]:
                raw_model = row[model_column].strip()
                if raw_model not in MODELS or raw_model in by_model:
                    raise ValueError(
                        f"Unexpected or repeated model in {regime_name}/{benchmark}: {raw_model}"
                    )
                values: list[float | None] = []
                for column in language_columns:
                    raw_score = row[column].strip() if column < len(row) else ""
                    score = float(raw_score) if raw_score else None
                    if score is not None and (not math.isfinite(score) or not 0 <= score <= 1):
                        raise ValueError(
                            f"Invalid F1 in {regime_name}/{benchmark}/{raw_model}: {score}"
                        )
                    values.append(score)
                by_model[raw_model] = values
            if set(by_model) != set(MODELS):
                raise ValueError(f"Missing model rows in {regime_name}/{benchmark}")

            results[regime_name][benchmark] = {
                language: [by_model[model][language_index] for model in MODELS]
                for language_index, language in enumerate(LANGUAGES)
            }
    return results


def draw_panel(axis: plt.Axes, results: Results, benchmark: str, language: str, compact: bool) -> int:
    profiles = [
        (regime, color, linestyle, marker, results[regime][benchmark][language])
        for _, regime, color, linestyle, marker in REGIMES
    ]
    available = [profile for profile in profiles if any(value is not None for value in profile[4])]
    if not available:
        axis.set_axis_off()
        axis.text(
            0.5, 0.54, "N/A", transform=axis.transAxes,
            ha="center", va="center", fontsize=9 if compact else 17,
            fontweight="semibold", color="#596579",
        )
        axis.text(
            0.5, 0.37, "No Arabic data", transform=axis.transAxes,
            ha="center", va="center", fontsize=5.3 if compact else 8,
            color="#596579",
        )
        return 0

    axis.set_theta_offset(math.pi / 2)
    axis.set_theta_direction(-1)
    axis.set_ylim(0, 1)
    axis.set_xticks(ANGLES, labels=SPOKE_CODES)
    axis.tick_params(axis="x", pad=1.0 if compact else 2.0, labelsize=5 if compact else 7)
    for label, angle in zip(axis.get_xticklabels(), ANGLES):
        if 0 < angle < math.pi:
            label.set_horizontalalignment("left")
        elif math.pi < angle < 2 * math.pi:
            label.set_horizontalalignment("right")
        else:
            label.set_horizontalalignment("center")
        label.set_color("#233041")
    axis.set_yticks([0.25, 0.5, 0.75, 1.0])
    axis.set_yticklabels([])
    axis.tick_params(length=0)
    axis.grid(color="#D7DFE7", linewidth=0.4 if compact else 0.65)
    axis.spines["polar"].set_color("#8190A0")
    axis.spines["polar"].set_linewidth(0.6 if compact else 0.9)

    for _, color, linestyle, marker, scores in available:
        radii = [math.nan if score is None else score for score in scores]
        axis.plot(
            ANGLES + ANGLES[:1], radii + radii[:1],
            color=color, linestyle=linestyle,
            linewidth=1.0 if compact else 1.6,
            marker=marker, markersize=2.2 if compact else 3.5,
            markerfacecolor="white", markeredgewidth=0.75 if compact else 1.1,
            zorder=3,
        )
    return len(available)


def render_grid(
    results: Results,
    languages: tuple[str, ...],
    output_dir: Path,
    stem: str,
    title: str,
    compact: bool,
) -> None:
    width, height = (7.2, 4.45) if compact else (23.0, 8.7)
    figure, axes = plt.subplots(
        len(BENCHMARKS), len(languages),
        subplot_kw={"projection": "polar"},
        figsize=(width, height),
        squeeze=False,
    )
    figure.patch.set_facecolor("white")
    figure.subplots_adjust(
        left=0.09 if compact else 0.045,
        right=0.975 if compact else 0.985,
        bottom=0.065 if compact else 0.06,
        top=0.68 if compact else 0.76,
        wspace=0.48 if compact else 0.25,
        hspace=0.66 if compact else 0.42,
    )

    for row_index, (_, benchmark) in enumerate(BENCHMARKS):
        for column_index, language in enumerate(languages):
            draw_panel(axes[row_index, column_index], results, benchmark, language, compact)

    figure.text(
        0.5, 0.985, title, ha="center", va="top",
        fontsize=10.5 if compact else 17, fontweight="semibold",
    )
    handles = [
        Line2D([0], [0], color=color, linestyle=linestyle, marker=marker,
               markerfacecolor="white", linewidth=1.5 if compact else 2,
               markersize=4 if compact else 6, label=name)
        for _, name, color, linestyle, marker in REGIMES
    ]
    figure.legend(
        handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.947),
        ncol=3, frameon=False, fontsize=7 if compact else 11,
        handlelength=2.3 if compact else 2.9, columnspacing=1.2 if compact else 2.0,
    )
    figure.text(
        0.5, 0.883 if compact else 0.893,
        "Model spokes clockwise from top:  XR = XLM-R Base  |  CL = ConLID  |  FT = fastText LID-176",
        ha="center", va="top", fontsize=6.2 if compact else 10,
        color="#3F4B5A",
    )
    figure.text(
        0.5, 0.851 if compact else 0.864,
        "GL = GlotLID v3  |  NL = NLLB LID-218  |  OL = OpenLID-v3",
        ha="center", va="top", fontsize=6.2 if compact else 10,
        color="#3F4B5A",
    )
    figure.text(
        0.5, 0.817 if compact else 0.830,
        "F1 radial scale: 0–1 (rings every 0.25)  |  N/A omitted; measured zero at centre",
        ha="center", va="top", fontsize=6.1 if compact else 9,
        color="#596579",
    )

    title_y = 0.734 if compact else 0.792
    for column_index, language in enumerate(languages):
        box = axes[0, column_index].get_position()
        figure.text(
            box.x0 + box.width / 2, title_y,
            language.replace("-", "\n"),
            ha="center", va="center", fontsize=6.3 if compact else 9,
            fontweight="semibold", linespacing=0.9,
        )
    for row_index, (_, benchmark) in enumerate(BENCHMARKS):
        box = axes[row_index, 0].get_position()
        figure.text(
            0.028 if compact else 0.015, box.y0 + box.height / 2,
            benchmark, ha="center", va="center", rotation=90,
            fontsize=8 if compact else 12, fontweight="semibold",
        )

    pdf_path = output_dir / f"{stem}.pdf"
    png_path = output_dir / f"{stem}.png"
    figure.savefig(pdf_path, metadata={"Title": title})
    figure.savefig(png_path, dpi=300)
    plt.close(figure)
    print(f"PDF: {pdf_path}")
    print(f"PNG: {png_path}")


def render_flores_showcase(results: Results, output_dir: Path) -> None:
    """Make the four compact FLORES+ panels used in the main paper."""
    figure, axes = plt.subplots(
        1, len(SHOWCASE_LANGUAGES), subplot_kw={"projection": "polar"},
        figsize=(7.2, 2.65), squeeze=False,
    )
    figure.patch.set_facecolor("white")
    figure.subplots_adjust(left=0.045, right=0.96, bottom=0.12, top=0.69, wspace=0.27)
    for column, language in enumerate(SHOWCASE_LANGUAGES):
        draw_panel(axes[0, column], results, "FLORES+", language, compact=True)
        axes[0, column].tick_params(axis="x", labelsize=6.1)
        box = axes[0, column].get_position()
        figure.text(
            box.x0 + box.width / 2, 0.785, language.replace("-", "\n"),
            ha="center", va="center", fontsize=7.2, fontweight="semibold", linespacing=0.9,
        )
    handles = [
        Line2D([0], [0], color=color, linestyle=linestyle, marker=marker,
               markerfacecolor="white", linewidth=1.5, markersize=4, label=name)
        for _, name, color, linestyle, marker in REGIMES
    ]
    figure.legend(
        handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.995),
        ncol=3, frameon=False, fontsize=7.3, handlelength=2.5, columnspacing=1.4,
    )
    stem = "radar_flores_four_languages_three_regimes"
    title = "FLORES+ F1: Sinhala, Pali, Sanskrit and English"
    pdf_path = output_dir / f"{stem}.pdf"
    png_path = output_dir / f"{stem}.png"
    figure.savefig(pdf_path, metadata={"Title": title})
    figure.savefig(png_path, dpi=300)
    plt.close(figure)
    print(f"PDF: {pdf_path}")
    print(f"PNG: {png_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--showcase-only", action="store_true",
                        help="Generate only the four FLORES+ panels for the main paper")
    args = parser.parse_args()

    plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42})
    results = read_results(args.csv)
    counts = Counter(
        sum(any(score is not None for score in results[regime][benchmark][language])
            for _, regime, *_ in REGIMES)
        for _, benchmark in BENCHMARKS for language in LANGUAGES
    )
    if sum(counts.values()) != 33 or counts != {3: 26, 2: 6, 0: 1}:
        raise ValueError(f"Unexpected panel coverage: {dict(counts)}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if not args.showcase_only:
        render_grid(
            results, LANGUAGES, args.output_dir, "radar_grid_three_regimes_3x11",
            "Per-language F1 across three adaptation regimes", compact=False,
        )
        render_grid(
            results, LANGUAGES[:6], args.output_dir, "radar_grid_three_regimes_languages_1-6",
            "Per-language F1 (languages 1–6)", compact=True,
        )
        render_grid(
            results, LANGUAGES[6:], args.output_dir, "radar_grid_three_regimes_languages_7-11",
            "Per-language F1 (languages 7–11)", compact=True,
        )
    render_flores_showcase(results, args.output_dir)
    print(f"Panels: 33 (3 traces: {counts[3]}, 2 traces: {counts[2]}, N/A: {counts[0]})")


if __name__ == "__main__":
    main()
