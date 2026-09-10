import sys
import os
import json
import fasttext
import pandas as pd
from sklearn.metrics import f1_score, accuracy_score, classification_report

def main():
    train_csv = "data_pipeline/datasets/finetuning/train_11lang_uniform.csv"
    train_txt = "data/phase2_eval/fasttext_train_11lang.txt"
    model_path = "models/fasttext_11lang_scratch.bin"
    os.makedirs("models", exist_ok=True)
    os.makedirs("data/phase2_eval", exist_ok=True)

    print("Converting train_11lang_uniform.csv to fastText format...")
    df_train = pd.read_csv(train_csv)
    with open(train_txt, "w", encoding="utf-8") as f:
        for _, row in df_train.iterrows():
            text = str(row["text"]).replace("\n", " ").strip()
            label = str(row["label"]).strip()
            f.write(f"__label__{label} {text}\n")
    print(f"Saved {len(df_train)} rows to {train_txt}")

    print("Training fastText from scratch on 11 languages...")
    model = fasttext.train_supervised(
        input=train_txt,
        lr=0.5,
        epoch=10,
        wordNgrams=2,
        minn=2,
        maxn=5,
        dim=256,
        loss="softmax",
        thread=8
    )
    model.save_model(model_path)
    print(f"Model saved to {model_path}")

    benchmarks = {
        "flores_plus": "data/phase2_eval/eval_flores_plus_11lang.csv",
        "wili-2018": "data/phase2_eval/eval_wili_2018_11lang.csv",
        "commonlid": "data/phase2_eval/eval_commonlid_11lang.csv"
    }

    results = {}
    classes = [
        "Sinh-Sinh", "Pali-Sinh", "San-Sinh", "San-Deva",
        "Eng-Latn", "Tam-Taml", "Hin-Deva", "Ben-Beng",
        "Ara-Arab", "Fre-Latn", "Ger-Latn"
    ]

    for bname, bpath in benchmarks.items():
        print(f"\nEvaluating fastText on {bname} ({bpath})...")
        df_test = pd.read_csv(bpath)
        texts = [str(t).replace("\n", " ").strip() for t in df_test["text"].tolist()]
        y_true = df_test["label"].tolist()

        preds = model.predict(texts, k=1)
        y_pred = [p[0].replace("__label__", "") for p in preds[0]]

        acc = accuracy_score(y_true, y_pred)
        macro_f1 = f1_score(y_true, y_pred, labels=classes, average="macro", zero_division=0)
        
        per_class_f1 = {}
        for c in classes:
            y_t = [1 if y == c else 0 for y in y_true]
            y_p = [1 if p == c else 0 for p in y_pred]
            per_class_f1[c] = round(f1_score(y_t, y_p, zero_division=0), 4)

        results[bname] = {
            "accuracy": round(acc, 4),
            "macro_f1": round(macro_f1, 4),
            "per_class_f1": per_class_f1
        }
        print(f"{bname} => Accuracy: {acc:.4f}, Macro-F1: {macro_f1:.4f}")

    out_json = "data/phase2_eval/fasttext_11lang_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved fastText results to {out_json}")

if __name__ == "__main__":
    main()
