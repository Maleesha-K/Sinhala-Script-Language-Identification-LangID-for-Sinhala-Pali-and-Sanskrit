"""Train ContinualLID (stock FastText LID-176 + leaf surgery) on the 11-language rehearsal dataset.

Dataset:
- train_11lang_uniform.csv (99,000 samples: 9,000 per class across 11 classes)
- val_11lang_uniform.csv   (11,000 samples: 1,000 per class across 11 classes)

Benchmark on:
- FLORES+ (eval_flores_plus_11lang.csv)
- WiLI-2018 (eval_wili_2018_11lang.csv)
- CommonLID (eval_commonlid_11lang.csv)

Populates row 34 in Comparison Tables - New Method.csv ("Finetune using all languages").
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import time
import random
import unicodedata
import pandas as pd
import numpy as np
import torch
from torch.utils.data import DataLoader
from tqdm.auto import tqdm
from sklearn.metrics import accuracy_score, f1_score

from data_pipeline.fasttext_continual.model import ContinualLID, pack_features
from data_pipeline.fasttext_continual.data import EncodedDataset, collate
from data_pipeline.fasttext_continual.features import single_line

CLASSES_11 = [
    "Sinh-Sinh", "Pali-Sinh", "San-Sinh", "San-Deva",
    "Eng-Latn", "Tam-Taml", "Hin-Deva", "Ben-Beng",
    "Ara-Arab", "Fre-Latn", "Ger-Latn"
]

BCP_TO_MODEL = {
    "Sinh-Sinh": "si",
    "Pali-Sinh": "pi",
    "San-Sinh": "sa",
    "San-Deva": "sa",
    "Eng-Latn": "en",
    "Tam-Taml": "ta",
    "Hin-Deva": "hi",
    "Ben-Beng": "bn",
    "Ara-Arab": "ar",
    "Fre-Latn": "fr",
    "Ger-Latn": "de"
}

LANG_TO_11 = {
    "si": "Sinh-Sinh",
    "pi": "Pali-Sinh",
    "en": "Eng-Latn",
    "ta": "Tam-Taml",
    "hi": "Hin-Deva",
    "bn": "Ben-Beng",
    "ar": "Ara-Arab",
    "fr": "Fre-Latn",
    "de": "Ger-Latn",
}

def detect_script(text):
    for char in text:
        name = unicodedata.name(char, "")
        if "SINHALA" in name:
            return "Sinh"
        elif "DEVANAGARI" in name:
            return "Deva"
        elif "TAMIL" in name:
            return "Taml"
        elif "BENGALI" in name:
            return "Beng"
        elif "ARABIC" in name:
            return "Arab"
        elif "LATIN" in name:
            return "Latn"
    return "Unknown"

def map_pred_to_11(pred_lang, text):
    if pred_lang == "sa":
        script = detect_script(text)
        if script == "Sinh":
            return "San-Sinh"
        elif script == "Deva":
            return "San-Deva"
        else:
            return "San-Sinh"
    return LANG_TO_11.get(pred_lang, pred_lang)

def load_11lang_records(csv_path):
    df = pd.read_csv(csv_path)
    records = []
    for _, row in df.iterrows():
        text = str(row["text"]).strip()
        if not text:
            continue
        label = str(row["label"]).strip()
        model_label = BCP_TO_MODEL.get(label)
        if not model_label:
            continue
        records.append({
            "text": single_line(text),
            "model_label": model_label,
            "eval_group": label
        })
    return records

def evaluate_on_benchmark(model, csv_path, bname):
    print(f"\n--- Evaluating on {bname} ({csv_path}) ---")
    df = pd.read_csv(csv_path)
    texts = [single_line(str(t)) for t in df["text"].tolist()]
    y_true = df["label"].tolist()

    model.eval()
    raw_preds, scores = model.predict(texts, batch_size=128)
    pred_langs = [p[0] for p in raw_preds]

    y_pred = [map_pred_to_11(plang, t) for plang, t in zip(pred_langs, texts)]

    acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, labels=CLASSES_11, average="macro", zero_division=0)

    per_class_f1 = {}
    for c in CLASSES_11:
        yt = [1 if y == c else 0 for y in y_true]
        yp = [1 if p == c else 0 for p in y_pred]
        per_class_f1[c] = round(f1_score(yt, yp, zero_division=0), 4)

    print(f"Accuracy: {acc:.4f}, Macro-F1: {macro_f1:.4f}")
    for c in CLASSES_11:
        support = sum(1 for y in y_true if y == c)
        print(f"  {c:15s} support={support:5d} F1={per_class_f1[c]:.4f}")

    return {
        "accuracy": round(acc, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class_f1": per_class_f1
    }

def main():
    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    init_dir = "data_pipeline/models/continual/exp01/init177"
    train_csv = "data_pipeline/datasets/finetuning/train_11lang_uniform.csv"
    val_csv = "data_pipeline/datasets/finetuning/val_11lang_uniform.csv"
    out_dir = "data_pipeline/models/continual/11lang_rehearsal_exp"
    os.makedirs(out_dir, exist_ok=True)

    print(f"Loading untrained ContinualLID from {init_dir}...")
    model = ContinualLID.from_pretrained(init_dir)

    print(f"Loading training data from {train_csv} (11 languages)...")
    train_records = load_11lang_records(train_csv)
    print(f"Loaded {len(train_records)} training records across 11 classes.")

    print(f"Loading validation data from {val_csv} (11 languages)...")
    val_records = load_11lang_records(val_csv)
    print(f"Loaded {len(val_records)} validation records.")

    print("\nEncoding training dataset...")
    train_set = EncodedDataset(train_records, model, balance="none", description="Train encoding")
    val_set = EncodedDataset(val_records, model, balance="none", description="Val encoding")
    val_loader = DataLoader(val_set, batch_size=64, shuffle=False, collate_fn=collate)

    epochs = 5
    lr = 0.5
    batch_size = 64
    optimizer = torch.optim.SGD(model.parameters(), lr=lr, momentum=0, weight_decay=0)

    print(f"\nStarting 11-language rehearsal training: {epochs} epochs, lr={lr}, batch_size={batch_size}...")
    best_val_acc = 0.0

    for epoch in range(1, epochs + 1):
        model.train()
        generator = torch.Generator().manual_seed(seed + epoch)
        loader = DataLoader(train_set, batch_size=batch_size, shuffle=True,
                            generator=generator, collate_fn=collate)
        total_loss, total_samples = 0.0, 0
        pbar = tqdm(loader, desc=f"Epoch {epoch}/{epochs}")
        for ids, offsets, targets, weights in pbar:
            optimizer.zero_grad()
            losses = model.nll(ids, offsets, targets)
            loss = (losses * weights).mean()
            loss.backward()
            optimizer.step()
            total_loss += float(loss.detach()) * targets.numel()
            total_samples += targets.numel()
            pbar.set_postfix(loss=f"{total_loss/total_samples:.4f}")

        # Evaluate on validation
        model.eval()
        val_correct, val_total = 0, 0
        with torch.no_grad():
            for ids, offsets, targets, _ in val_loader:
                scores = model.leaf_log_scores(ids, offsets)
                preds = scores.argmax(dim=1)
                val_correct += (preds == targets).sum().item()
                val_total += targets.numel()
        val_acc = val_correct / val_total
        print(f"Epoch {epoch} complete: Train Loss = {total_loss/total_samples:.4f}, Val 11-Lang Accuracy = {val_acc:.4f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_path = os.path.join(out_dir, "best")
            model.save_pretrained(best_path)
            print(f"  * Saved new best model to {best_path}")

    print("\nTraining complete! Loading best model for hybrid benchmark evaluation...")
    best_model = ContinualLID.from_pretrained(os.path.join(out_dir, "best"))

    benchmarks = {
        "flores_plus": "data/phase2_eval/eval_flores_plus_11lang.csv",
        "wili_2018": "data/phase2_eval/eval_wili_2018_11lang.csv",
        "commonlid": "data/phase2_eval/eval_commonlid_11lang.csv"
    }

    all_results = {}
    for bname, bpath in benchmarks.items():
        all_results[bname] = evaluate_on_benchmark(best_model, bpath, bname)

    results_file = os.path.join(out_dir, "rehearsal_11lang_benchmark_results.json")
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nAll benchmark results saved to {results_file}!")

if __name__ == "__main__":
    main()
