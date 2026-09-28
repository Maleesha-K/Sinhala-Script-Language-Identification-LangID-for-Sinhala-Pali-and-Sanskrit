"""Build the 11 language-script group dataset for continued fine-tuning.

Produces, under data_pipeline/datasets/finetuning/:
    train_mixed_11groups.jsonl
    val_mixed_11groups.jsonl
    dataset_11groups_report.json

Groups (label is ISO-3; script and group disambiguate the two Sanskrit groups):

    Sinhala-Sinh   sin/Sinh   existing target train.csv / val.csv
    Pali-Sinh      pli/Sinh   existing target train.csv / val.csv
    Sanskrit-Sinh  san/Sinh   existing target train.csv / val.csv
    Sanskrit-Deva  san/Deva   surajp/sanskrit_classic (combined.txt)
    English-Latn   eng/Latn   CohereLabs/aya_dataset
    Tamil-Taml     tam/Taml   CohereLabs/aya_dataset
    Hindi-Deva     hin/Deva   CohereLabs/aya_dataset
    Bengali-Beng   ben/Beng   CohereLabs/aya_dataset
    Arabic-Arab    arb/Arab   CohereLabs/aya_dataset
    French-Latn    fra/Latn   CohereLabs/aya_dataset
    German-Latn    deu/Latn   CohereLabs/aya_dataset

The existing target train/val assignments are preserved verbatim -- the target
files are never recombined and re-split. Benchmark corpora (FLORES+, CommonLID,
WiLI-2018) are read only for overlap reporting, never for training or
validation.

Run from data_pipeline/:  python scripts/05.finetune_dataset/build_11groups.py
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import sys
import unicodedata
from collections import Counter, defaultdict

import pandas as pd

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

SEED = 42
MAX_PER_LANG = 5000          # cap for Aya languages and Sanskrit-Deva
VAL_FRACTION = 0.10          # 90/10 train/val on the newly sampled sources
MIN_CHARS = 15               # quality floor, matching the repo data dictionary
MIN_WORDS = 3
MAX_WORDS = 60
SCRIPT_PURITY = 0.70         # min fraction of letters in the expected script

OUTPUT_DIR = "datasets/finetuning"
TARGET_TRAIN_CSV = os.path.join(OUTPUT_DIR, "train.csv")
TARGET_VAL_CSV = os.path.join(OUTPUT_DIR, "val.csv")

SANSKRIT_DEVA_FILE = "datasets/raw_download/sanskrit_classic/combined.txt"
SANSKRIT_DEVA_URL = (
    "https://github.com/parmarsuraj99/hf_datasets/raw/master/"
    "sanskrit_classic/combined.zip"
)
SANSKRIT_DEVA_SHA256 = (
    "0505787526bae65e239e03a94870d1f2f9db4094da2f60c0035db9afcd298a28"
)

AYA_DATASET = "CohereLabs/aya_dataset"

TRAIN_OUT = os.path.join(OUTPUT_DIR, "train_mixed_11groups.jsonl")
VAL_OUT = os.path.join(OUTPUT_DIR, "val_mixed_11groups.jsonl")
REPORT_OUT = os.path.join(OUTPUT_DIR, "dataset_11groups_report.json")

# Target CSV label (lowercase) -> (group, iso3, script)
TARGET_GROUPS = {
    "sinhala": ("Sinhala-Sinh", "sin", "Sinh"),
    "pali": ("Pali-Sinh", "pli", "Sinh"),
    "sanskrit": ("Sanskrit-Sinh", "san", "Sinh"),
}

# Aya language_code -> (group, iso3, script)
AYA_GROUPS = {
    "eng": ("English-Latn", "eng", "Latn"),
    "tam": ("Tamil-Taml", "tam", "Taml"),
    "hin": ("Hindi-Deva", "hin", "Deva"),
    "ben": ("Bengali-Beng", "ben", "Beng"),
    "arb": ("Arabic-Arab", "arb", "Arab"),
    "fra": ("French-Latn", "fra", "Latn"),
    "deu": ("German-Latn", "deu", "Latn"),
}

SANSKRIT_DEVA_GROUP = ("Sanskrit-Deva", "san", "Deva")

EXPECTED_GROUPS = (
    [g for g, _, _ in TARGET_GROUPS.values()]
    + [SANSKRIT_DEVA_GROUP[0]]
    + [g for g, _, _ in AYA_GROUPS.values()]
)

# Unicode ranges used for script verification.
SCRIPT_RANGES = {
    "Sinh": [(0x0D80, 0x0DFF)],
    "Deva": [(0x0900, 0x097F), (0xA8E0, 0xA8FF)],
    "Taml": [(0x0B80, 0x0BFF)],
    "Beng": [(0x0980, 0x09FF)],
    "Arab": [(0x0600, 0x06FF), (0x0750, 0x077F), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)],
    "Latn": [(0x0041, 0x005A), (0x0061, 0x007A), (0x00C0, 0x024F)],
}

# Benchmark / test files consulted for overlap only. Never used as training or
# validation data, and never modified.
BENCHMARK_FILES = [
    "datasets/preprocessed/flores_plus.jsonl",
    "datasets/preprocessed/commonlid.jsonl",
    "datasets/preprocessed/wili-2018.jsonl",
]
TEST_FILES = [
    "test_dataset_folder/test.csv",
    "../data/Nadil/test.csv",
]

_WS = re.compile(r"\s+")


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def norm_key(text: str) -> str:
    """NFC-normalized, whitespace-collapsed, casefolded comparison key.

    Used only for dedup / conflict / overlap comparison. The saved `text`
    field always keeps the original string.
    """
    return _WS.sub(" ", unicodedata.normalize("NFC", str(text))).strip().casefold()


def script_fraction(text: str, script: str) -> float:
    """Fraction of the alphabetic characters that belong to `script`."""
    ranges = SCRIPT_RANGES[script]
    letters = [c for c in str(text) if c.isalpha()]
    if not letters:
        return 0.0
    hits = sum(
        1 for c in letters if any(lo <= ord(c) <= hi for lo, hi in ranges)
    )
    return hits / len(letters)


def dominant_script(text: str) -> str:
    """Best-matching known script for a string, for diagnosing mixed records."""
    scores = {s: script_fraction(text, s) for s in SCRIPT_RANGES}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Zyyy"


def passes_quality(text: str) -> tuple[bool, str]:
    """Length / word-count gate shared by the newly sampled sources."""
    if text is None:
        return False, "empty_text"
    collapsed = _WS.sub(" ", str(text)).strip()
    if not collapsed:
        return False, "empty_text"
    if len(collapsed) < MIN_CHARS:
        return False, "too_short_chars"
    words = collapsed.split(" ")
    if len(words) < MIN_WORDS:
        return False, "too_few_words"
    if len(words) > MAX_WORDS:
        return False, "too_many_words"
    return True, ""


def grouped_split(items, key_fn, val_fraction, rng):
    """Split `items` into (train, val) without ever splitting a key group.

    Groups are shuffled, then assigned to validation until the fraction is
    met, so identical / related texts always land on the same side.
    """
    buckets = defaultdict(list)
    for item in items:
        buckets[key_fn(item)].append(item)

    keys = sorted(buckets)
    rng.shuffle(keys)

    target_val = int(round(len(items) * val_fraction))
    val, train, n_val = [], [], 0
    for key in keys:
        bucket = buckets[key]
        if n_val + len(bucket) <= target_val:
            val.extend(bucket)
            n_val += len(bucket)
        else:
            train.extend(bucket)
    # Guarantee non-empty validation when the data allows it.
    if not val and len(keys) > 1:
        first = buckets[keys[0]]
        val.extend(first)
        train = [i for i in train if i not in first]
    return train, val


def fail(message: str) -> None:
    print(f"\nFATAL: {message}", file=sys.stderr)
    sys.exit(1)


# --------------------------------------------------------------------------
# 1. Target groups: preserve the existing train / val assignments
# --------------------------------------------------------------------------

def load_target_records(csv_path: str, split: str, exclusions: list) -> list:
    if not os.path.exists(csv_path):
        fail(
            f"required target input missing: {csv_path}. "
            "Run setup_finetune_data.ipynb first. Refusing to emit an "
            "Aya-only dataset."
        )
    df = pd.read_csv(csv_path)

    records = []
    for row in df.to_dict(orient="records"):
        raw_label = str(row.get("label", "")).strip().lower()
        if raw_label not in TARGET_GROUPS:
            exclusions.append(
                {
                    "split": split,
                    "source": "target_csv",
                    "id": row.get("id"),
                    "reason": f"unmapped_label:{raw_label}",
                }
            )
            continue
        group, iso3, script = TARGET_GROUPS[raw_label]

        text = row.get("text")
        if text is None or not str(text).strip() or str(text).lower() == "nan":
            exclusions.append(
                {
                    "split": split,
                    "group": group,
                    "id": row.get("id"),
                    "reason": "empty_text",
                }
            )
            continue

        # Degenerate rows: the target CSVs carry a number of bare numerals
        # and punctuation-only strings (e.g. "400", "5") inherited from the
        # upstream corpora. They contain no letters at all, so they cannot
        # carry a language or script signal, and a bare integer collides
        # trivially with benchmark rows. Documented removal, not silent.
        if not any(c.isalpha() for c in str(text)):
            exclusions.append(
                {
                    "split": split,
                    "group": group,
                    "id": row.get("id"),
                    "reason": "no_alphabetic_content",
                    "text": str(text)[:60],
                }
            )
            continue

        records.append(
            {
                "text": str(text),
                "label": iso3,
                "script": script,
                "group": group,
                "source": row.get("source"),
                "orig_id": row.get("id"),
                "subcorpus": row.get("subcorpus"),
                "group_id": row.get("group_id"),
                "provenance": f"target_{split}_csv:{os.path.basename(csv_path)}",
                "split": split,
            }
        )
    return records


# --------------------------------------------------------------------------
# 2. Aya groups: reproducible random sampling with grouped splitting
# --------------------------------------------------------------------------

def load_aya_records(exclusions: list, script_warnings: list, stats: dict) -> list:
    from datasets import load_dataset

    print(f"Loading {AYA_DATASET} (train split)...")
    ds = load_dataset(AYA_DATASET, split="train")

    try:
        from huggingface_hub import HfApi

        revision = HfApi().dataset_info(AYA_DATASET).sha
    except Exception:
        revision = None
    stats["aya_revision"] = revision

    # Collect eligible candidates per language, deduplicating on the
    # normalized key before any sampling happens.
    pools = {lang: {} for lang in AYA_GROUPS}
    seen_per_lang = {lang: set() for lang in AYA_GROUPS}
    per_lang_counts = Counter()
    drop_counts = defaultdict(Counter)

    for idx, row in enumerate(ds):
        lang = row.get("language_code")
        if lang not in AYA_GROUPS:
            continue
        per_lang_counts[lang] += 1

        group, iso3, script = AYA_GROUPS[lang]
        text = row.get("inputs")

        ok, reason = passes_quality(text)
        if not ok:
            drop_counts[lang][reason] += 1
            continue

        frac = script_fraction(text, script)
        if frac < SCRIPT_PURITY:
            drop_counts[lang]["script_mismatch"] += 1
            if len(script_warnings) < 200:
                script_warnings.append(
                    {
                        "group": group,
                        "expected_script": script,
                        "observed_dominant_script": dominant_script(text),
                        "expected_script_fraction": round(frac, 4),
                        "aya_row_index": idx,
                        "text_preview": _WS.sub(" ", str(text)).strip()[:120],
                    }
                )
            continue

        key = norm_key(text)
        if key in seen_per_lang[lang]:
            drop_counts[lang]["duplicate_in_source"] += 1
            continue
        seen_per_lang[lang].add(key)

        pools[lang][key] = {
            "text": str(text),
            "label": iso3,
            "script": script,
            "group": group,
            "source": "aya_dataset",
            "orig_id": row.get("id"),
            "aya_row_index": idx,
            "aya_language_code": lang,
            "provenance": f"{AYA_DATASET}@train",
        }

    # Reproducible sampling: seed 42, sorted keys for a deterministic base
    # order, then random.sample -- never "first N rows".
    records = []
    for lang, (group, _, _) in AYA_GROUPS.items():
        pool = pools[lang]
        keys = sorted(pool)
        rng = random.Random(f"{SEED}:{lang}")
        take = min(MAX_PER_LANG, len(keys))
        chosen_keys = rng.sample(keys, take) if take < len(keys) else list(keys)

        chosen = [pool[k] for k in chosen_keys]
        split_rng = random.Random(f"{SEED}:split:{lang}")
        train, val = grouped_split(
            chosen, lambda r: norm_key(r["text"]), VAL_FRACTION, split_rng
        )
        for rec in train:
            rec["split"] = "train"
        for rec in val:
            rec["split"] = "val"
        records.extend(train + val)

        stats["aya_per_language"][lang] = {
            "group": group,
            "rows_seen_in_source": per_lang_counts[lang],
            "eligible_unique": len(keys),
            "sampled": take,
            "cap": MAX_PER_LANG,
            "capped": take == MAX_PER_LANG and len(keys) > MAX_PER_LANG,
            "train": len(train),
            "val": len(val),
            "dropped": dict(drop_counts[lang]),
        }
        for reason, n in drop_counts[lang].items():
            exclusions.append(
                {"group": group, "source": "aya_dataset", "reason": reason, "count": n}
            )
        print(
            f"  {group:<14} eligible={len(keys):>6} sampled={take:>5} "
            f"train={len(train):>5} val={len(val):>5}"
        )

    return records


# --------------------------------------------------------------------------
# 3. Sanskrit-Devanagari: independently sourced, same cap and split policy
# --------------------------------------------------------------------------

def load_sanskrit_deva_records(exclusions, script_warnings, stats):
    group, iso3, script = SANSKRIT_DEVA_GROUP

    if not os.path.exists(SANSKRIT_DEVA_FILE):
        stats["sanskrit_deva"] = {
            "status": "MISSING",
            "expected_file": SANSKRIT_DEVA_FILE,
            "documented_source": "surajp/sanskrit_classic",
            "note": (
                "Aya supplies no Sanskrit at all, and this file was not found. "
                "Download combined.zip from the URL in the report and extract "
                "it to the expected path."
            ),
        }
        print(f"  WARNING: {SANSKRIT_DEVA_FILE} not found -- {group} will be EMPTY.")
        return []

    print(f"Loading Sanskrit-Devanagari from {SANSKRIT_DEVA_FILE}...")
    with open(SANSKRIT_DEVA_FILE, encoding="utf-8") as fh:
        lines = fh.readlines()

    sha = hashlib.sha256(
        open(SANSKRIT_DEVA_FILE, "rb").read()
    ).hexdigest()

    pool, seen = {}, set()
    drops = Counter()
    for idx, raw in enumerate(lines):
        ok, reason = passes_quality(raw)
        if not ok:
            drops[reason] += 1
            continue
        frac = script_fraction(raw, script)
        if frac < SCRIPT_PURITY:
            drops["script_mismatch"] += 1
            if len(script_warnings) < 400:
                script_warnings.append(
                    {
                        "group": group,
                        "expected_script": script,
                        "observed_dominant_script": dominant_script(raw),
                        "expected_script_fraction": round(frac, 4),
                        "line_index": idx,
                        "text_preview": _WS.sub(" ", raw).strip()[:120],
                    }
                )
            continue
        key = norm_key(raw)
        if key in seen:
            drops["duplicate_in_source"] += 1
            continue
        seen.add(key)
        pool[key] = {
            "text": raw.strip(),
            "label": iso3,
            "script": script,
            "group": group,
            "source": "sanskrit_classic",
            "orig_id": f"sanskrit_classic_line_{idx}",
            "line_index": idx,
            "provenance": "surajp/sanskrit_classic:combined.txt",
        }

    keys = sorted(pool)
    rng = random.Random(f"{SEED}:san_deva")
    take = min(MAX_PER_LANG, len(keys))
    chosen_keys = rng.sample(keys, take) if take < len(keys) else list(keys)
    chosen = [pool[k] for k in chosen_keys]

    split_rng = random.Random(f"{SEED}:split:san_deva")
    train, val = grouped_split(
        chosen, lambda r: norm_key(r["text"]), VAL_FRACTION, split_rng
    )
    for rec in train:
        rec["split"] = "train"
    for rec in val:
        rec["split"] = "val"

    stats["sanskrit_deva"] = {
        "status": "OK",
        "documented_source": "surajp/sanskrit_classic",
        "upstream_url": SANSKRIT_DEVA_URL,
        "zip_sha256": SANSKRIT_DEVA_SHA256,
        "extracted_file": SANSKRIT_DEVA_FILE,
        "extracted_sha256": sha,
        "has_predefined_splits": False,
        "split_policy": "90/10 grouped split applied (no upstream splits exist)",
        "raw_lines": len(lines),
        "eligible_unique": len(keys),
        "sampled": take,
        "cap": MAX_PER_LANG,
        "train": len(train),
        "val": len(val),
        "dropped": dict(drops),
    }
    for reason, n in drops.items():
        exclusions.append(
            {"group": group, "source": "sanskrit_classic", "reason": reason, "count": n}
        )
    print(
        f"  {group:<14} eligible={len(keys):>6} sampled={take:>5} "
        f"train={len(train):>5} val={len(val):>5}"
    )
    return train + val


# --------------------------------------------------------------------------
# 4. Validation
# --------------------------------------------------------------------------

def validate(train_recs, val_recs, report):
    findings = {}

    groups_train = Counter(r["group"] for r in train_recs)
    groups_val = Counter(r["group"] for r in val_recs)
    all_groups = set(groups_train) | set(groups_val)

    findings["expected_group_count"] = len(EXPECTED_GROUPS)
    findings["observed_group_count"] = len(all_groups)
    findings["unexpected_groups"] = sorted(all_groups - set(EXPECTED_GROUPS))
    findings["missing_groups"] = sorted(set(EXPECTED_GROUPS) - all_groups)
    findings["groups_with_empty_train"] = sorted(
        g for g in EXPECTED_GROUPS if groups_train.get(g, 0) == 0
    )
    findings["groups_with_empty_val"] = sorted(
        g for g in EXPECTED_GROUPS if groups_val.get(g, 0) == 0
    )

    # Missing / empty text
    findings["empty_text_in_output"] = sum(
        1 for r in train_recs + val_recs if not str(r.get("text", "")).strip()
    )

    # Duplicates within each split and across splits
    train_keys = [norm_key(r["text"]) for r in train_recs]
    val_keys = [norm_key(r["text"]) for r in val_recs]
    findings["duplicates_within_train"] = len(train_keys) - len(set(train_keys))
    findings["duplicates_within_val"] = len(val_keys) - len(set(val_keys))
    findings["overlap_train_val"] = len(set(train_keys) & set(val_keys))

    # Conflicting labels for identical normalized text
    by_key = defaultdict(set)
    for r in train_recs + val_recs:
        by_key[norm_key(r["text"])].add((r["label"], r["script"]))
    conflicts = {k: sorted(v) for k, v in by_key.items() if len(v) > 1}
    findings["conflicting_label_keys"] = len(conflicts)
    findings["conflicting_examples"] = [
        {"text_preview": k[:100], "labels": [list(x) for x in v]}
        for k, v in list(conflicts.items())[:20]
    ]

    # Script verification on the emitted records
    script_issues = Counter()
    for r in train_recs + val_recs:
        if script_fraction(r["text"], r["script"]) < SCRIPT_PURITY:
            script_issues[r["group"]] += 1
    findings["records_below_script_purity"] = dict(script_issues)

    # Overlap with held-out benchmark and target test files (read-only)
    output_keys = set(train_keys) | set(val_keys)
    overlap = {}
    checked, not_found = [], []

    for path in BENCHMARK_FILES:
        if not os.path.exists(path):
            not_found.append(path)
            continue
        keys = set()
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    keys.add(norm_key(json.loads(line).get("text", "")))
                except json.JSONDecodeError:
                    continue
        hits = output_keys & keys
        overlap[path] = {"benchmark_rows": len(keys), "overlapping_texts": len(hits)}
        checked.append(path)

    for path in TEST_FILES:
        if not os.path.exists(path):
            not_found.append(path)
            continue
        df = pd.read_csv(path)
        keys = {norm_key(t) for t in df["text"].dropna()}
        hits = output_keys & keys
        overlap[path] = {"test_rows": len(keys), "overlapping_texts": len(hits)}
        checked.append(path)

    findings["overlap_checks"] = overlap
    findings["test_files_checked"] = checked
    findings["test_files_not_found"] = not_found
    findings["total_held_out_overlap"] = sum(
        v.get("overlapping_texts", 0) for v in overlap.values()
    )

    report["validation"] = findings
    return findings


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    if not os.path.exists("Makefile") and os.path.exists("../../Makefile"):
        os.chdir("../../")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    random.seed(SEED)

    exclusions: list = []
    script_warnings: list = []
    quarantined: list = []
    stats: dict = {"aya_per_language": {}}

    print("=" * 72)
    print("Building the 11 language-script group fine-tuning dataset")
    print("=" * 72)

    # 1. Target groups, splits preserved exactly as they are on disk.
    print("\n[1/4] Target groups (existing splits preserved)")
    target_train = load_target_records(TARGET_TRAIN_CSV, "train", exclusions)
    target_val = load_target_records(TARGET_VAL_CSV, "val", exclusions)
    if not target_train or not target_val:
        fail("target train/val produced no records -- aborting.")
    print(f"  train={len(target_train)}  val={len(target_val)} (assignments untouched)")

    # 2. Aya groups.
    print("\n[2/4] Aya groups (seed 42, random sampling, cap 5000)")
    aya = load_aya_records(exclusions, script_warnings, stats)

    # 3. Sanskrit-Devanagari.
    print("\n[3/4] Sanskrit-Devanagari")
    san_deva = load_sanskrit_deva_records(exclusions, script_warnings, stats)

    # Assemble, dropping cross-source duplicates and quarantining conflicts.
    all_records = target_train + target_val + aya + san_deva

    by_key = defaultdict(list)
    for rec in all_records:
        by_key[norm_key(rec["text"])].append(rec)

    kept = []
    for key, recs in by_key.items():
        labels = {(r["label"], r["script"]) for r in recs}
        if len(labels) > 1:
            # Conflicting label for identical text: quarantine, never guess.
            for r in recs:
                quarantined.append(
                    {
                        "text_preview": r["text"][:120],
                        "group": r["group"],
                        "label": r["label"],
                        "script": r["script"],
                        "source": r["source"],
                        "reason": "conflicting_label_for_identical_text",
                    }
                )
            exclusions.append(
                {
                    "reason": "conflicting_label_quarantined",
                    "count": len(recs),
                    "labels": sorted(str(x) for x in labels),
                }
            )
            continue
        if len(recs) > 1:
            # Same text, same label: keep one, prefer a target record and
            # keep it on whichever split it already belongs to.
            recs.sort(key=lambda r: (0 if "target_" in r["provenance"] else 1,))
            exclusions.append(
                {
                    "reason": "duplicate_text_across_sources",
                    "count": len(recs) - 1,
                    "group": recs[0]["group"],
                }
            )
        kept.append(recs[0])

    train_recs = [r for r in kept if r["split"] == "train"]
    val_recs = [r for r in kept if r["split"] == "val"]

    random.Random(SEED).shuffle(train_recs)
    random.Random(SEED + 1).shuffle(val_recs)

    # 4. Validate, then write.
    print("\n[4/4] Validation")
    report: dict = {}
    findings = validate(train_recs, val_recs, report)

    def emit(records, path):
        with open(path, "w", encoding="utf-8") as fh:
            for r in records:
                out = {
                    "text": r["text"],
                    "label": r["label"],
                    "script": r["script"],
                    "group": r["group"],
                    "source": r["source"],
                    "provenance": r["provenance"],
                }
                for extra in (
                    "orig_id",
                    "subcorpus",
                    "group_id",
                    "aya_row_index",
                    "aya_language_code",
                    "line_index",
                ):
                    if r.get(extra) is not None and not (
                        isinstance(r.get(extra), float) and pd.isna(r[extra])
                    ):
                        out[extra] = r[extra]
                fh.write(json.dumps(out, ensure_ascii=False) + "\n")

    emit(train_recs, TRAIN_OUT)
    emit(val_recs, VAL_OUT)

    per_group = {}
    tr = Counter(r["group"] for r in train_recs)
    va = Counter(r["group"] for r in val_recs)
    for g in EXPECTED_GROUPS:
        per_group[g] = {"train": tr.get(g, 0), "val": va.get(g, 0)}

    per_source = {
        "train": dict(Counter(str(r["source"]) for r in train_recs)),
        "val": dict(Counter(str(r["source"]) for r in val_recs)),
    }

    report.update(
        {
            "generated_by": "scripts/05.finetune_dataset/build_11groups.py",
            "seed": SEED,
            "sampling": {
                "max_per_language": MAX_PER_LANG,
                "val_fraction": VAL_FRACTION,
                "method": (
                    "random.sample over the deduplicated eligible pool with a "
                    "per-language seeded RNG derived from seed 42 -- not the "
                    "first N rows"
                ),
                "grouping": (
                    "Target groups keep their existing train/val assignment "
                    "verbatim. Newly sampled sources use a grouped split keyed "
                    "on the NFC-normalized, whitespace-collapsed text, so "
                    "identical texts never straddle the split."
                ),
                "quality_filters": {
                    "min_chars": MIN_CHARS,
                    "min_words": MIN_WORDS,
                    "max_words": MAX_WORDS,
                    "script_purity_threshold": SCRIPT_PURITY,
                },
                "no_row_duplication": True,
            },
            "sources": {
                "target": {
                    "train_csv": TARGET_TRAIN_CSV,
                    "val_csv": TARGET_VAL_CSV,
                    "splits_preserved": True,
                },
                "aya": {
                    "dataset": AYA_DATASET,
                    "split": "train",
                    "field": "inputs",
                    "revision": stats.get("aya_revision"),
                },
                "sanskrit_deva": stats.get("sanskrit_deva"),
            },
            "aya_per_language": stats["aya_per_language"],
            "groups": EXPECTED_GROUPS,
            "counts": {
                "per_group": per_group,
                "per_source": per_source,
                "train_total": len(train_recs),
                "val_total": len(val_recs),
            },
            "exclusions": exclusions,
            "quarantined": quarantined[:200],
            "quarantined_total": len(quarantined),
            "script_warnings": script_warnings[:200],
            "script_warnings_total": len(script_warnings),
            "benchmark_policy": (
                "FLORES+, CommonLID and WiLI-2018 are read only for overlap "
                "reporting. They are never used for training, validation, "
                "early stopping or model selection, and are not modified."
            ),
            "outputs": {
                "train": TRAIN_OUT,
                "val": VAL_OUT,
                "report": REPORT_OUT,
            },
            "reproduction": {
                "commands": [
                    "cd data_pipeline",
                    "python scripts/05.finetune_dataset/build_11groups.py",
                ],
                "notebook": (
                    "scripts/05.finetune_dataset/setup_rehearsal_data_aya.ipynb"
                ),
                "sanskrit_deva_fetch": [
                    f"curl -L -o combined.zip {SANSKRIT_DEVA_URL}",
                    "unzip combined.zip -d datasets/raw_download/sanskrit_classic",
                ],
            },
        }
    )

    with open(REPORT_OUT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    # Console summary
    print(f"\n  groups observed: {findings['observed_group_count']}/11")
    print(f"  empty train groups: {findings['groups_with_empty_train'] or 'none'}")
    print(f"  empty val groups:   {findings['groups_with_empty_val'] or 'none'}")
    print(f"  dup within train/val: {findings['duplicates_within_train']}"
          f"/{findings['duplicates_within_val']}")
    print(f"  train/val overlap: {findings['overlap_train_val']}")
    print(f"  label conflicts quarantined: {len(quarantined)}")
    print(f"  held-out overlap total: {findings['total_held_out_overlap']}")

    print("\n" + "=" * 72)
    print(f"{'Group':<16}{'Train':>10}{'Val':>10}")
    print("-" * 72)
    for g in EXPECTED_GROUPS:
        print(f"{g:<16}{per_group[g]['train']:>10}{per_group[g]['val']:>10}")
    print("-" * 72)
    print(f"{'TOTAL':<16}{len(train_recs):>10}{len(val_recs):>10}")
    print("=" * 72)
    print(f"\nWrote:\n  {TRAIN_OUT}\n  {VAL_OUT}\n  {REPORT_OUT}")


if __name__ == "__main__":
    main()
