"""Sync the paper's Phase 2 LaTeX tables with the latest comparison CSV.

Run from anywhere: python scripts/sync_phase2_latex_tables.py
The three CSV sections are authoritative; missing scores remain N/A and real zeros
remain numeric zeros. Phase 1 baseline rows in the overview are left unchanged.
"""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "Comparison Tables - New Method (2).csv"
PAPER_PATH = ROOT / "Overleaf" / "acl_latex.tex"
SNIPPET_PATH = ROOT / "Overleaf" / "latest_phase2_tables.tex"

REGIMES = (
    ("zero shot results", "Zero-shot results"),
    ("finetune using 3 languages", "Target-only fine-tuning"),
    ("finetune using all languages", "All-language rehearsal"),
)
BENCHMARKS = (
    ("flores_plus", "FLORES+", "flores_full"),
    ("commonlid", "CommonLID", "common_full"),
    ("wili-2018", "WiLI-2018", "wili_full"),
)
LANGUAGES = (
    "Sinhala-Sinh", "Pali-Sinh", "Sanskrit-Sinh", "Sanskrit-Deva",
    "English-Latn", "Tamil-Taml", "Hindi-Deva", "Bengali-Beng",
    "Arabic-Arab", "French-Latn", "German-Latn",
)
LATEX_LANGUAGES = (
    "Sinh-Sinh", "Pali-Sinh", "San-Sinh", "San-Deva", "Eng-Latn",
    "Tam-Taml", "Hin-Deva", "Ben-Beng", "Ara-Arab", "Fre-Latn",
    "Ger-Latn",
)
MODELS = (
    "XLM-R Base", "ConLID", "fastText LID-176", "GlotLID v3",
    "NLLB LID-218", "OpenLID-v3",
)


def read_scores() -> dict[str, dict[str, dict[str, list[str]]]]:
    with CSV_PATH.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.reader(stream))
    section_indices = []
    for prefix, name in REGIMES:
        matches = [
            index for index, row in enumerate(rows)
            if any(cell.strip().lower().startswith(prefix) for cell in row)
        ]
        if len(matches) != 1:
            raise ValueError(f"Expected one {name} section, found {len(matches)}")
        section_indices.append(matches[0])
    if section_indices != sorted(section_indices):
        raise ValueError("Regimes are not in the expected order")

    data: dict[str, dict[str, dict[str, list[str]]]] = {}
    for regime_index, (_, regime_name) in enumerate(REGIMES):
        start = section_indices[regime_index]
        end = section_indices[regime_index + 1] if regime_index < 2 else len(rows)
        headers = [
            index for index in range(start + 1, end)
            if sum(cell.strip().lower() == "model" for cell in rows[index]) == 3
        ]
        if len(headers) != 1:
            raise ValueError(f"Expected one three-benchmark header in {regime_name}")
        header_index = headers[0]
        header = rows[header_index]
        model_columns = [index for index, cell in enumerate(header)
                         if cell.strip().lower() == "model"]
        if header_index + len(MODELS) >= end:
            raise ValueError(f"Missing model rows in {regime_name}")
        data[regime_name] = {}

        for block_index, (raw_benchmark, benchmark, _) in enumerate(BENCHMARKS):
            column = model_columns[block_index]
            block_end = model_columns[block_index + 1] if block_index < 2 else len(header)
            names_above = [
                cell.strip().lower() for row in rows[start + 1:header_index]
                for cell in row[column:block_end]
            ]
            if raw_benchmark not in names_above:
                raise ValueError(f"Wrong benchmark block in {regime_name}: {benchmark}")
            actual_languages = tuple(
                "Arabic-Arab" if header[column + 1 + j].strip().startswith("Arabic-Arab")
                else header[column + 1 + j].strip()
                for j in range(len(LANGUAGES))
            )
            if actual_languages != LANGUAGES:
                raise ValueError(f"Language order changed in {regime_name}/{benchmark}")

            by_model: dict[str, list[str]] = {}
            for row in rows[header_index + 1:header_index + 1 + len(MODELS)]:
                model = row[column].strip()
                if model not in MODELS or model in by_model:
                    raise ValueError(f"Unexpected model in {regime_name}/{benchmark}: {model}")
                values = [row[column + offset].strip() for offset in range(1, 13)]
                for raw in values:
                    if not raw:
                        continue
                    try:
                        score = Decimal(raw)
                    except InvalidOperation as exc:
                        raise ValueError(f"Invalid score {raw!r}") from exc
                    if not score.is_finite() or not 0 <= score <= 1:
                        raise ValueError(f"Out-of-range F1 {raw!r}")
                by_model[model] = values
            if tuple(by_model) != MODELS:
                raise ValueError(f"Model order changed in {regime_name}/{benchmark}")
            data[regime_name][benchmark] = by_model

    for _, regime in REGIMES:
        for _, benchmark, _ in BENCHMARKS:
            for model in MODELS:
                values = data[regime][benchmark][model]
                if benchmark == "WiLI-2018" and values[8]:
                    raise ValueError("WiLI-2018 Arabic must remain N/A")
                if regime == "Zero-shot results" and any(values[j] for j in (1, 2)):
                    raise ValueError("Zero-shot Pali-Sinh/Sanskrit-Sinh must remain N/A")
    return data


def latex_value(raw: str, *, macro: bool = False) -> str:
    if not raw:
        return "--"
    return f"{Decimal(raw):.4f}"


def summary_table(data: dict[str, dict[str, dict[str, list[str]]]]) -> str:
    rows = [
        r"\begin{table}[!htbp]",
        r"\centering",
        r"\footnotesize",
        r"\setlength{\tabcolsep}{2.5pt}",
        r"\caption{Overall CSV-reported Macro-F1 across the three Phase 2 hybrid benchmarks. Foundation-model rows show all-language rehearsal; from-scratch baseline results are unchanged. WiLI-2018 has no Arabic class.}",
        r"\label{tab:sota_overall_summary}",
        r"\resizebox{\columnwidth}{!}{%",
        r"\begin{tabular}{lccc}",
        r"\toprule",
        r"\textbf{Model Family} & \textbf{FLORES+} & \textbf{CommonLID} & \textbf{WiLI-18} \\",
        r"\midrule",
        r"\multicolumn{4}{l}{\textit{\textbf{From-Scratch Baselines} (Trained on Uniform 110k)}} \\",
        r"Multinomial NB & 0.9332 & 0.9342 & 0.9785 \\",
        r"Linear SVM & 0.9342 & 0.8895 & 0.9679 \\",
        r"Char $n$-gram + LogReg & 0.9298 & 0.8907 & 0.9750 \\",
        r"fastText (from scratch) & 0.9281 & 0.8758 & 0.9584 \\",
        r"XGBoost & 0.9181 & 0.8734 & 0.9215 \\",
        r"Char-CNN (1D-CNN) & 0.9177 & 0.8398 & 0.8790 \\",
        r"Char-BiGRU (Recurrent) & 0.9111 & 0.8166 & 0.8770 \\",
        r"\midrule",
        r"\multicolumn{4}{l}{\textit{\textbf{Foundation Models: All-Language Rehearsal}}} \\",
    ]
    for model in MODELS:
        scores = [latex_value(data["All-language rehearsal"][benchmark][model][-1], macro=True)
                  for _, benchmark, _ in BENCHMARKS]
        scores = [r"\textbf{" + score + "}" if (model, index) in {
            ("XLM-R Base", 0), ("fastText LID-176", 1),
            ("XLM-R Base", 2),
        } else score for index, score in enumerate(scores)]
        rows.append(f"{model} & " + " & ".join(scores) + r" \\")
    rows += [r"\bottomrule", r"\end{tabular}%", "}", r"\end{table}"]
    return "\n".join(rows)


def appendix_tables(data: dict[str, dict[str, dict[str, list[str]]]]) -> str:
    rows = [
        r"\begin{table*}[p]",
        r"\centering",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{1.4pt}",
        r"\renewcommand{\arraystretch}{0.78}",
    ]
    header = " & ".join([r"\textbf{Model}"] +
                        [rf"\textbf{{{name}}}" for name in LATEX_LANGUAGES] +
                        [r"\textbf{Macro F1}"]) + r" \\"
    for benchmark_index, (_, benchmark, label) in enumerate(BENCHMARKS):
        if benchmark_index:
            rows.append(r"\vspace{4pt}")
        rows += [
            rf"\caption{{{benchmark} hybrid benchmark: per-language F1 and Macro-F1 across three training regimes.}}",
            rf"\label{{tab:{label}}}",
            r"\begin{tabular}{l ccc cccccccc c}",
            r"\toprule",
            header,
            r"\midrule",
        ]
        for regime_index, (_, regime) in enumerate(REGIMES):
            if regime_index:
                rows.append(r"\midrule")
            rows.append(rf"\multicolumn{{13}}{{l}}{{\textit{{{regime}}}}} \\")
            for model in MODELS:
                values = data[regime][benchmark][model]
                formatted = [latex_value(raw) for raw in values[:11]]
                formatted.append(latex_value(values[11], macro=True))
                rows.append(model + " & " + " & ".join(formatted) + r" \\")
        rows += [r"\bottomrule", r"\end{tabular}"]
    rows.append(r"\end{table*}")
    return "\n".join(rows)


def appendix_radar_figure() -> str:
    return "\n".join([
        r"\clearpage",
        r"\begin{figure*}[p]",
        r"\centering",
        r"\includegraphics[width=0.96\textwidth]{figures/radar_grid_three_regimes_languages_1-6.pdf}",
        r"\par\vspace{-3pt}",
        r"\includegraphics[width=0.96\textwidth]{figures/radar_grid_three_regimes_languages_7-11.pdf}",
        r"\caption{All 33 benchmark--language radar panels. The upper block contains languages 1--6 and the lower block languages 7--11; each block has FLORES+, CommonLID, and WiLI-2018 rows. Colored lines show zero-shot, target-only fine-tuning, and all-language rehearsal. WiLI-2018 Arabic is N/A.}",
        r"\label{fig:radar_all_33}",
        r"\end{figure*}",
        r"\clearpage",
    ])


def replace_between(text: str, opening: str, closing: str, replacement: str) -> str:
    start = text.index(opening)
    end = text.index(closing, start) + len(closing)
    return text[:start] + replacement + text[end:]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layout-check", type=Path,
                        help="Write a standalone A4 two-column LaTeX file for table fit checks")
    args = parser.parse_args()
    data = read_scores()
    summary = summary_table(data)
    appendix = appendix_tables(data)
    text = PAPER_PATH.read_text(encoding="utf-8")
    summary_start = text.index(r"\subsection{Benchmark Performance Overview}")
    appendix_start = text.index(r"\section{Detailed Hybrid Benchmark Results Across 11 Languages}")
    if summary_start >= appendix_start:
        raise ValueError("Paper sections have moved")
    before_summary, remainder = text[:summary_start], text[summary_start:]
    remainder = replace_between(remainder, r"\begin{table}[!htbp]", r"\end{table}", summary)
    text = before_summary + remainder
    appendix_start = text.index(r"\section{Detailed Hybrid Benchmark Results Across 11 Languages}")
    before_appendix, remainder = text[:appendix_start], text[appendix_start:]
    first_table = remainder.index(r"\begin{table*}[p]")
    next_section = remainder.index(r"\section{Dataset Provenance", first_table)
    remainder = remainder[:first_table] + appendix + "\n\n" + appendix_radar_figure() + "\n\n" + remainder[next_section:]
    updated_paper = before_appendix + remainder
    showcase_start = updated_paper.index(r"\begin{figure*}[!t]", updated_paper.index(r"\section{Phase 2:"))
    showcase_end = updated_paper.index(r"\end{figure*}", showcase_start) + len(r"\end{figure*}")
    showcase = updated_paper[showcase_start:showcase_end]
    PAPER_PATH.write_text(updated_paper, encoding="utf-8")
    SNIPPET_PATH.write_text(
        "% Paste this first block over the Benchmark Performance Overview table.\n"
        + summary + "\n\n"
        + "% Paste this four-panel FLORES+ figure near the start of Phase 2.\n"
        + showcase + "\n\n"
        + "% Paste this combined block over the Detailed Hybrid Benchmark Results appendix tables.\n"
        + appendix + "\n\n"
        + "% Paste this figure immediately after the combined appendix table.\n"
        + appendix_radar_figure() + "\n", encoding="utf-8",
    )
    if args.layout_check:
        args.layout_check.write_text(
            "\n".join([
                r"\documentclass[11pt,twocolumn]{article}",
                r"\usepackage[a4paper,margin=2.5cm]{geometry}",
                r"\usepackage{booktabs}",
                r"\begin{document}",
                appendix,
                r"\clearpage",
                r"\end{document}",
            ]) + "\n", encoding="utf-8",
        )
        print(f"Standalone table check: {args.layout_check}")
    print(f"Updated: {PAPER_PATH}")
    print(f"Paste-ready tables: {SNIPPET_PATH}")
    print("Imported 3 regimes x 3 benchmarks x 6 models from the CSV")


if __name__ == "__main__":
    main()
