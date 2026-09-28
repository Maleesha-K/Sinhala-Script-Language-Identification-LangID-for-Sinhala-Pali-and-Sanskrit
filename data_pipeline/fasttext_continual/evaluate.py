"""All-output inference; language-level F1 and per-script-group accuracy."""

import argparse
from collections import Counter
from pathlib import Path

import torch
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from tqdm.auto import tqdm

from .data import GROUPS, load_records
from .features import single_line
from .model import ContinualLID, write_json


def metrics(records, predictions):
    gold = [r["model_label"] for r in records]
    # All model outputs compete at inference. Macro-F1 averages only the
    # languages represented by GOLD examples. Out-of-set predictions still
    # count as false negatives for their true language.
    labels = sorted(set(gold))
    p, r, f, s = precision_recall_fscore_support(gold, predictions, labels=labels, zero_division=0)
    groups = {}
    for group in sorted({row["eval_group"] for row in records}):
        indices = [i for i, row in enumerate(records) if row["eval_group"] == group]
        correct = sum(gold[i] == predictions[i] for i in indices)
        groups[group] = {"support": len(indices), "correct": correct, "accuracy": correct / len(indices)}
    return {"examples": len(gold), "accuracy": float(accuracy_score(gold, predictions)),
            "language_macro_f1": float(f.mean()), "macro_languages": labels,
            "per_language": {label: {"precision": float(p[i]), "recall": float(r[i]),
                                      "f1": float(f[i]), "support": int(s[i])} for i, label in enumerate(labels)},
            "per_group": groups,
            "predictions_outside_gold_languages": sum(x not in labels for x in predictions),
            "prediction_counts": dict(Counter(predictions)),
            "group_metric_note": "Group accuracy equals recall on that subset; gold script is never used for prediction."}


@torch.no_grad()
def evaluate_encoded(model, loader, records):
    model.eval()
    predictions = []
    for ids, offsets, _, _ in loader:
        scores = model.leaf_log_scores(ids.to(model.device), offsets.to(model.device))
        predictions.extend(model.labels[i] for i in scores.argmax(1).cpu().tolist())
    result = metrics(records, predictions)
    result["output_labels"] = len(model.labels)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--checkpoint")
    source.add_argument("--base-bin")
    parser.add_argument("--data", required=True, help="JSONL/CSV with text,label and group/script metadata")
    parser.add_argument("--out", required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()
    torch.set_num_threads(args.threads)
    records = load_records(args.data)
    texts = [r["text"] for r in records]
    predictions = []
    if args.base_bin:
        import fasttext
        native = fasttext.load_model(args.base_bin)
        for start in tqdm(range(0, len(texts), args.batch_size), desc="Native baseline"):
            # List API avoids the older scalar wrapper's NumPy-2 copy=False issue.
            labels, _ = native.predict([single_line(x) for x in texts[start:start + args.batch_size]], k=1)
            predictions.extend(row[0].removeprefix("__label__") for row in labels)
        nlabels = len(native.get_labels())
    else:
        model = ContinualLID.from_pretrained(args.checkpoint, device=args.device)
        for start in tqdm(range(0, len(texts), args.batch_size), desc="Continued model"):
            labels, _ = model.predict(texts[start:start + args.batch_size], batch_size=args.batch_size)
            predictions.extend(row[0] for row in labels)
        nlabels = len(model.labels)
    result = metrics(records, predictions)
    result.update(output_labels=nlabels, data=str(Path(args.data)), checkpoint=args.checkpoint or args.base_bin)
    write_json(args.out, result)
    print(f"Accuracy={result['accuracy']:.6f}; language macro-F1={result['language_macro_f1']:.6f}; outputs={nlabels}")
    for group, row in result["per_group"].items():
        print(f"{group:18s} n={row['support']:6d} accuracy={row['accuracy']:.6f}")


if __name__ == "__main__":
    main()
