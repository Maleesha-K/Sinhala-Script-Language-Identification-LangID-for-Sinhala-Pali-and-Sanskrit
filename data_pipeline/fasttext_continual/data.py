"""Dataset adapters, label mapping and cached FEATURE IDs (not frozen vectors)."""

import csv
import hashlib
import json
import random
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset
from tqdm.auto import tqdm

from .features import single_line
from .model import pack_features

GROUPS = {
    "Sinhala-Sinh": ("si", "Sinh"), "Pali-Sinh": ("pi", "Sinh"),
    "Sanskrit-Sinh": ("sa", "Sinh"), "Sanskrit-Deva": ("sa", "Deva"),
    "English-Latn": ("en", "Latn"), "Tamil-Taml": ("ta", "Taml"),
    "Hindi-Deva": ("hi", "Deva"), "Bengali-Beng": ("bn", "Beng"),
    "Arabic-Arab": ("ar", "Arab"), "French-Latn": ("fr", "Latn"),
    "German-Latn": ("de", "Latn"),
}
LANGUAGES = sorted({v[0] for v in GROUPS.values()})
LANG_ALIAS = {
    "sin": "si", "sinhala": "si", "sinh": "si",
    "pli": "pi", "pali": "pi", "san": "sa", "sanskrit": "sa",
    "eng": "en", "english": "en", "tam": "ta", "tamil": "ta",
    "hin": "hi", "hindi": "hi", "ben": "bn", "bengali": "bn",
    "arb": "ar", "ara": "ar", "arabic": "ar",
    "fra": "fr", "fre": "fr", "french": "fr",
    "deu": "de", "ger": "de", "german": "de",
}
LANG_ALIAS.update({lang: lang for lang in LANGUAGES})
GROUP_LOOKUP = {(lang, script.lower()): group for group, (lang, script) in GROUPS.items()}


def decode_tag(tag):
    tag = str(tag).removeprefix("__label__").strip().lower().replace("_", "-")
    parts = tag.split("-")
    if parts[0] not in LANG_ALIAS:
        raise ValueError(f"Unmapped language tag {tag!r}; supply an explicit adapter")
    return LANG_ALIAS[parts[0]], parts[1] if len(parts) == 2 else None


def load_records(path, require_groups=True):
    path = Path(path)
    records = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = csv.DictReader(f) if path.suffix.lower() == ".csv" else (json.loads(line) for line in f if line.strip())
        for number, row in enumerate(rows, 1):
            text = row.get("text")
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"{path}, row {number}: empty or non-string text")
            original_label = row.get("label")
            if original_label is None:
                raise ValueError(f"{path}, row {number}: missing label")
            language, label_script = decode_tag(original_label)
            explicit_group = row.get("group") or row.get("eval_group")
            script = row.get("script") or label_script
            if explicit_group:
                group_lang, group_script = decode_tag(explicit_group)
                if group_lang != language or not group_script:
                    raise ValueError(f"{path}, row {number}: group/label conflict")
                if script and script.lower() != group_script:
                    raise ValueError(f"{path}, row {number}: group/script conflict")
                script = group_script
            if not script and language != "sa":
                script = next(s for l, s in GROUPS.values() if l == language)
            group = GROUP_LOOKUP.get((language, str(script).lower()))
            if not group and require_groups:
                raise ValueError(f"{path}, row {number}: missing/unknown script group; Sanskrit requires Sinh or Deva")
            record = dict(row)
            record.update(text=single_line(text), model_label=language,
                          eval_group=group or language, original_label=original_label)
            records.append(record)
    if not records:
        raise ValueError(f"Empty dataset: {path}")
    return records


def text_key(text):
    normalized = " ".join(unicodedata.normalize("NFC", text).split())
    return hashlib.sha256(normalized.encode("utf-8")).digest()


def check_splits(train, val):
    result, seen = {}, []
    for name, records in [("train", train), ("val", val)]:
        counts = Counter(r["eval_group"] for r in records)
        if set(counts) != set(GROUPS):
            raise ValueError(f"{name} must contain exactly the 11 expected groups; got {dict(counts)}")
        keys = [text_key(r["text"]) for r in records]
        duplicate_count = len(keys) - len(set(keys))
        if duplicate_count:
            raise ValueError(f"{name} has {duplicate_count} repeated normalized texts; fix the dataset first")
        seen.append(set(keys))
        result[name] = {"records": len(records), "groups": dict(counts)}
    overlap = len(seen[0] & seen[1])
    if overlap:
        raise ValueError(f"Train/validation overlap: {overlap} normalized texts")
    result["normalized_train_val_overlap"] = 0
    result["note"] = "Held-out benchmark checks belong to dataset_11groups_report.json; this trainer does not read test data."
    return result


def subset_per_group(records, limit, seed=42):
    if limit is None:
        return records
    if limit < 1:
        raise ValueError("Pilot size must be positive")
    groups = defaultdict(list)
    for record in records:
        groups[record["eval_group"]].append(record)
    rng, selected = random.Random(seed), []
    for group in sorted(groups):
        rows = groups[group]
        selected.extend(rng.sample(rows, min(limit, len(rows))))
    return selected


class EncodedDataset(Dataset):
    def __init__(self, records, model, balance="none", description="Encoding"):
        counts = Counter(r["eval_group"] for r in records)
        self.rows = []
        for r in tqdm(records, desc=description):
            features = np.asarray(model.encoder.encode(r["text"]), dtype=np.int32)
            target = model.label_to_id[r["model_label"]]
            weight = len(records) / (len(counts) * counts[r["eval_group"]]) if balance == "group" else 1.0
            self.rows.append((features, target, weight))

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        return self.rows[index]


def collate(batch):
    sequences, targets, weights = zip(*batch)
    ids, offsets = pack_features(sequences)
    return ids, offsets, torch.tensor(targets, dtype=torch.long), torch.tensor(weights, dtype=torch.float32)
