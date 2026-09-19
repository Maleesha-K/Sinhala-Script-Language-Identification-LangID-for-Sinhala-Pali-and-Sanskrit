"""
Phase 1: Closed-World Benchmark (Micro-Level Disambiguation)
Trains 7 strictly FROM-SCRATCH baseline models on the target training dataset (data/Nadil/train.csv)
and evaluates them consistently across:
  - Full Sentence
  - 5-Word Fragments
  - 3-Word Fragments
  - 1-Word Fragments

Models (7 From-Scratch):
  1. Multinomial Naive Bayes (Probabilistic ML)
  2. Linear SVM (Margin-based Linear ML)
  3. Char n-gram + Logistic Regression (Classic Frequency-based NLP)
  4. XGBoost (Tree-based Ensemble / Gradient Boosting)
  5. Char-CNN (Character-level Deep Learning from scratch)
  6. fastText (Trained from Scratch) (Subword embeddings from scratch)
  7. Char-BiGRU (Recurrent Deep Learning from scratch)
"""

import os
import sys
import json
import random
import subprocess
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, f1_score, classification_report
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

# Ensure unbuffered output
sys.stdout.reconfigure(line_buffering=True)

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)

OUTPUT_DIR = "results"
os.makedirs(OUTPUT_DIR, exist_ok=True)
CSV_RESULTS_PATH = os.path.join(OUTPUT_DIR, "phase1_baselines_consistent.csv")

# 1. Load Data
print("=" * 70, flush=True)
print("Loading Target Training and Testing Sets...", flush=True)
train_df = pd.read_csv("data/Nadil/train.csv")
test_df = pd.read_csv("data/Nadil/test.csv")

print(f"Train samples: {len(train_df)} -> {train_df['label'].value_counts().to_dict()}", flush=True)
print(f"Test samples:  {len(test_df)} -> {test_df['label'].value_counts().to_dict()}", flush=True)

# 2. Fragment Generation (Deterministic)
rng = random.Random(RANDOM_SEED)

def random_k_words(text, k):
    words = str(text).split()
    if len(words) <= k:
        return " ".join(words)
    start = rng.randint(0, len(words) - k)
    return " ".join(words[start:start + k])

print("\nGenerating Fragment Test Splits (5-word, 3-word, 1-word)...", flush=True)
test_splits = {
    "full": list(test_df["text"]),
    "5w": [random_k_words(t, 5) for t in test_df["text"]],
    "3w": [random_k_words(t, 3) for t in test_df["text"]],
    "1w": [random_k_words(t, 1) for t in test_df["text"]]
}

label_to_id = {"sinhala": 0, "pali": 1, "sanskrit": 2}
id_to_label = {0: "sinhala", 1: "pali", 2: "sanskrit"}

y_train = np.array([label_to_id[l] for l in train_df["label"]])
y_test = np.array([label_to_id[l] for l in test_df["label"]])

# Master results table
# Format: model_name -> split -> {acc, macro_f1}
all_model_results = {}

# 3. TF-IDF Vectorizer for Linear/Tree Models
print("\nFitting Character n-gram TF-IDF Vectorizer (2-4 n-grams, max 20,000 features)...", flush=True)
vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4), max_features=20000, sublinear_tf=True)
X_train_tfidf = vectorizer.fit_transform(train_df["text"])

X_test_tfidf_splits = {
    split: vectorizer.transform(texts) for split, texts in test_splits.items()
}

def evaluate_sklearn_model(name, model, X_train, y_train):
    print(f"\n--- Training {name} ---", flush=True)
    model.fit(X_train, y_train)
    all_model_results[name] = {}
    for split in ["full", "5w", "3w", "1w"]:
        preds = model.predict(X_test_tfidf_splits[split])
        acc = accuracy_score(y_test, preds)
        mf1 = f1_score(y_test, preds, average="macro")
        all_model_results[name][split] = {"accuracy": round(acc, 4), "macro_f1": round(mf1, 4)}
        print(f"  {name:30s} @ {split:4s} -> Acc: {acc:.4f}, Macro-F1: {mf1:.4f}", flush=True)

# 1. Multinomial Naive Bayes
evaluate_sklearn_model(
    "Multinomial NB",
    MultinomialNB(alpha=0.1),
    X_train_tfidf, y_train
)

# 2. Linear SVM
evaluate_sklearn_model(
    "Linear SVM",
    LinearSVC(C=1.0, random_state=RANDOM_SEED, max_iter=2000),
    X_train_tfidf, y_train
)

# 3. Char n-gram + Logistic Regression
evaluate_sklearn_model(
    "Char n-gram + LogReg",
    LogisticRegression(C=1.0, max_iter=1000, random_state=RANDOM_SEED),
    X_train_tfidf, y_train
)

# 4. XGBoost
evaluate_sklearn_model(
    "XGBoost",
    XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.2, random_state=RANDOM_SEED, tree_method="hist", n_jobs=-1),
    X_train_tfidf, y_train
)

# 5. fastText (Trained from Scratch)
print("\n--- Training fastText (Trained from Scratch) ---", flush=True)
fasttext_train_file = "data/Nadil/fasttext_scratch_train.txt"
with open(fasttext_train_file, "w", encoding="utf-8") as f:
    for text, label in zip(train_df["text"], train_df["label"]):
        clean_t = str(text).replace("\n", " ").strip()
        f.write(f"__label__{label} {clean_t}\n")

fasttext_eval_json = "data/Nadil/fasttext_eval_data.json"
eval_payload = {
    split: {
        "texts": test_splits[split],
        "labels": list(test_df["label"])
    }
    for split in ["full", "5w", "3w", "1w"]
}
with open(fasttext_eval_json, "w", encoding="utf-8") as f:
    json.dump(eval_payload, f)

fasttext_out_json = "data/Nadil/fasttext_scratch_out.json"
fasttext_cmd = [
    r"C:\Users\User\miniconda3\envs\langid\python.exe",
    "scripts/run_fasttext_scratch.py",
    fasttext_train_file,
    fasttext_eval_json,
    fasttext_out_json
]
subprocess.run(fasttext_cmd, check=True)

with open(fasttext_out_json, "r", encoding="utf-8") as f:
    ft_res = json.load(f)

all_model_results["fastText (re-trained)"] = {
    split: {"accuracy": ft_res[split]["accuracy"], "macro_f1": ft_res[split]["macro_f1"]}
    for split in ["full", "5w", "3w", "1w"]
}

# 6 & 7. Character-level Neural Networks (Char-CNN & Char-BiGRU)
print("\nPreparing Character Vocab for Neural Networks...", flush=True)
all_chars = sorted(list(set("".join(train_df["text"]))))
char2id = {c: i + 2 for i, c in enumerate(all_chars)}
char2id["<PAD>"] = 0
char2id["<UNK>"] = 1
VOCAB_SIZE = len(char2id)
MAX_LEN = 128

def encode_texts(texts):
    arr = np.zeros((len(texts), MAX_LEN), dtype=np.int64)
    for i, t in enumerate(texts):
        chars = [char2id.get(c, 1) for c in str(t)[:MAX_LEN]]
        arr[i, :len(chars)] = chars
    return torch.tensor(arr)

X_train_nn = encode_texts(train_df["text"])
y_train_nn = torch.tensor(y_train)

X_test_nn_splits = {
    split: encode_texts(test_splits[split]) for split in ["full", "5w", "3w", "1w"]
}
y_test_nn = torch.tensor(y_test)

train_dataset = TensorDataset(X_train_nn, y_train_nn)
train_loader = DataLoader(train_dataset, batch_size=256, shuffle=True)

# Char-CNN Architecture
class CharCNN(nn.Module):
    def __init__(self, vocab_size, emb_dim=64, n_filters=128, kernel_sizes=(2, 3, 4, 5), n_classes=3, dropout=0.3):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
        self.convs = nn.ModuleList([nn.Conv1d(emb_dim, n_filters, k) for k in kernel_sizes])
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(n_filters * len(kernel_sizes), n_classes)

    def forward(self, x):
        # x: [B, L] -> emb: [B, L, D] -> transpose: [B, D, L]
        emb = self.emb(x).transpose(1, 2)
        conv_outs = []
        for conv in self.convs:
            c = torch.relu(conv(emb))  # [B, n_filters, L - k + 1]
            pooled = torch.max(c, dim=2)[0]  # [B, n_filters]
            conv_outs.append(pooled)
        cat = self.dropout(torch.cat(conv_outs, dim=1))
        return self.fc(cat)

# Char-BiGRU Architecture
class CharBiGRU(nn.Module):
    def __init__(self, vocab_size, emb_dim=64, hidden=128, n_classes=3, dropout=0.3):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
        self.gru = nn.GRU(emb_dim, hidden, batch_first=True, bidirectional=True)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden * 2, n_classes)

    def forward(self, x):
        emb = self.emb(x)
        out, _ = self.gru(emb)
        pooled = torch.max(out, dim=1)[0]
        return self.fc(self.dropout(pooled))

def train_eval_neural_model(name, model, epochs=3):
    print(f"\n--- Training {name} from scratch ({epochs} epochs) ---", flush=True)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.002)
    
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for bx, by in train_loader:
            optimizer.zero_grad()
            logits = model(bx)
            loss = criterion(logits, by)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(by)
        print(f"  Epoch {epoch}/{epochs} - Loss: {total_loss / len(train_dataset):.4f}", flush=True)

    all_model_results[name] = {}
    model.eval()
    with torch.no_grad():
        for split in ["full", "5w", "3w", "1w"]:
            test_x = X_test_nn_splits[split]
            logits = model(test_x)
            preds = torch.argmax(logits, dim=1).numpy()
            acc = accuracy_score(y_test, preds)
            mf1 = f1_score(y_test, preds, average="macro")
            all_model_results[name][split] = {"accuracy": round(acc, 4), "macro_f1": round(mf1, 4)}
            print(f"  {name:30s} @ {split:4s} -> Acc: {acc:.4f}, Macro-F1: {mf1:.4f}", flush=True)

# Train Char-CNN
cnn_model = CharCNN(VOCAB_SIZE)
train_eval_neural_model("Char-CNN", cnn_model, epochs=3)

# Train Char-BiGRU
gru_model = CharBiGRU(VOCAB_SIZE)
train_eval_neural_model("Char-BiGRU", gru_model, epochs=3)

# 8. Compile Final Comparison Table
print("\n" + "=" * 90, flush=True)
print("PHASE 1: CLOSED-WORLD BENCHMARK (MICRO-LEVEL SCRIPT DISAMBIGUATION)", flush=True)
print("=" * 90, flush=True)

headers = ["Model", "Architecture", "Full Acc", "Full F1", "5w Acc", "5w F1", "3w Acc", "3w F1", "1w Acc", "1w F1"]
arch_map = {
    "Multinomial NB": "ML (Probabilistic)",
    "Linear SVM": "ML (Margin-based)",
    "Char n-gram + LogReg": "ML (Baseline)",
    "XGBoost": "Gradient Boosting",
    "fastText (re-trained)": "Subword Embeddings",
    "Char-CNN": "Deep Learning (1D-CNN)",
    "Char-BiGRU": "Deep Learning (BiGRU)"
}

table_rows = []
for model_name, arch in arch_map.items():
    res = all_model_results[model_name]
    row = [
        model_name,
        arch,
        res["full"]["accuracy"],
        res["full"]["macro_f1"],
        res["5w"]["accuracy"],
        res["5w"]["macro_f1"],
        res["3w"]["accuracy"],
        res["3w"]["macro_f1"],
        res["1w"]["accuracy"],
        res["1w"]["macro_f1"]
    ]
    table_rows.append(row)

res_df = pd.DataFrame(table_rows, columns=headers)
print(res_df.to_string(index=False), flush=True)

res_df.to_csv(CSV_RESULTS_PATH, index=False)
print(f"\nSaved complete consistent results to: {CSV_RESULTS_PATH}", flush=True)
