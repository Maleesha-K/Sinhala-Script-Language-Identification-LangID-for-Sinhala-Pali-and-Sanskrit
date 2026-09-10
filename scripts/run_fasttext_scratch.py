"""
Trains fastText from scratch on the target 3-way training set
and evaluates on full sentences, 5-word, 3-word, and 1-word fragment tests.
Uses Python environment: C:\\Users\\User\\miniconda3\\envs\\langid\\python.exe
"""

import sys
import os
import json
import fasttext
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, classification_report

train_txt = sys.argv[1]
eval_json = sys.argv[2]
out_json = sys.argv[3]

print("Training fastText from scratch on:", train_txt)
model = fasttext.train_supervised(
    input=train_txt,
    lr=0.5,
    epoch=25,
    wordNgrams=3,
    minn=2,
    maxn=5,
    dim=100,
    loss='softmax',
    seed=42,
    thread=4
)

with open(eval_json, "r", encoding="utf-8") as f:
    eval_data = json.load(f)

results = {}

for split_name in ["full", "5w", "3w", "1w"]:
    texts = eval_data[split_name]["texts"]
    y_true = eval_data[split_name]["labels"]
    
    # Predict
    clean_texts = [str(t).replace("\n", " ").strip() for t in texts]
    preds = model.predict(clean_texts)[0]
    y_pred = [p[0].replace("__label__", "") for p in preds]
    
    acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro")
    
    results[split_name] = {
        "accuracy": round(acc, 4),
        "macro_f1": round(macro_f1, 4),
        "report": classification_report(y_true, y_pred, output_dict=True)
    }
    print(f"fastText @ {split_name:4s} -> Acc: {acc:.4f}, Macro-F1: {macro_f1:.4f}")

with open(out_json, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("Saved fastText scratch results to:", out_json)
