import os
import sys
import time
import json
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from xgboost import XGBClassifier
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

CLASSES = [
    "Sinh-Sinh", "Pali-Sinh", "San-Sinh", "San-Deva",
    "Eng-Latn", "Tam-Taml", "Hin-Deva", "Ben-Beng",
    "Ara-Arab", "Fre-Latn", "Ger-Latn"
]
CLASS_TO_IDX = {c: i for i, c in enumerate(CLASSES)}
IDX_TO_CLASS = {i: c for i, c in enumerate(CLASSES)}

# Device setup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class CharVocabulary:
    def __init__(self, max_len=200):
        self.char2idx = {"<PAD>": 0, "<UNK>": 1}
        self.max_len = max_len

    def build_vocab(self, texts):
        for t in texts:
            for ch in str(t):
                if ch not in self.char2idx:
                    self.char2idx[ch] = len(self.char2idx)
        print(f"Built character vocabulary of size: {len(self.char2idx)}")

    def transform(self, texts):
        sequences = np.zeros((len(texts), self.max_len), dtype=np.int64)
        for i, t in enumerate(texts):
            s = str(t)[:self.max_len]
            for j, ch in enumerate(s):
                sequences[i, j] = self.char2idx.get(ch, 1)
        return sequences

class TextDataset(Dataset):
    def __init__(self, sequences, labels):
        self.sequences = torch.tensor(sequences, dtype=torch.long)
        self.labels = torch.tensor(labels, dtype=torch.long)

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]

class CharCNN(nn.Module):
    def __init__(self, vocab_size, emb_dim=64, num_classes=11):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
        self.conv1 = nn.Conv1d(emb_dim, 128, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(emb_dim, 128, kernel_size=5, padding=2)
        self.conv3 = nn.Conv1d(emb_dim, 128, kernel_size=7, padding=3)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.3)
        self.fc = nn.Linear(128 * 3, num_classes)

    def forward(self, x):
        emb = self.embedding(x).transpose(1, 2)
        c1 = self.relu(self.conv1(emb)).max(dim=2)[0]
        c2 = self.relu(self.conv2(emb)).max(dim=2)[0]
        c3 = self.relu(self.conv3(emb)).max(dim=2)[0]
        out = torch.cat([c1, c2, c3], dim=1)
        out = self.dropout(out)
        return self.fc(out)

class CharBiGRU(nn.Module):
    def __init__(self, vocab_size, emb_dim=64, hidden_dim=128, num_classes=11):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
        self.gru = nn.GRU(emb_dim, hidden_dim, num_layers=2, bidirectional=True, batch_first=True)
        self.dropout = nn.Dropout(0.3)
        self.fc = nn.Linear(hidden_dim * 2, num_classes)

    def forward(self, x):
        emb = self.embedding(x)
        out, h_n = self.gru(emb)
        rep = torch.cat([h_n[-2], h_n[-1]], dim=1)
        rep = self.dropout(rep)
        return self.fc(rep)

def evaluate_predictions(y_true, y_pred):
    acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, labels=CLASSES, average="macro", zero_division=0)
    per_class = {}
    for c in CLASSES:
        yt = [1 if y == c else 0 for y in y_true]
        yp = [1 if p == c else 0 for p in y_pred]
        per_class[c] = round(f1_score(yt, yp, zero_division=0), 4)
    return round(acc, 4), round(macro_f1, 4), per_class

def main():
    os.makedirs("results", exist_ok=True)
    os.makedirs("models", exist_ok=True)

    print("=" * 80)
    print(" PHASE 2: BENCHMARKING 7 FROM-SCRATCH BASELINES ON 11-LANGUAGE HYBRID DATASETS")
    print("=" * 80)

    # 1. Load Training Data
    train_path = "data_pipeline/datasets/finetuning/train_11lang_uniform.csv"
    print(f"Loading training data from {train_path}...")
    df_train = pd.read_csv(train_path)
    train_texts = df_train["text"].astype(str).tolist()
    train_labels = df_train["label"].astype(str).tolist()
    train_y_idx = [CLASS_TO_IDX[l] for l in train_labels]
    print(f"Loaded {len(train_texts)} training samples across {len(CLASSES)} classes.")

    # 2. Load Evaluation Benchmarks
    benchmarks = {
        "FLORES+": pd.read_csv("data/phase2_eval/eval_flores_plus_11lang.csv"),
        "WiLI-2018": pd.read_csv("data/phase2_eval/eval_wili_2018_11lang.csv"),
        "CommonLID": pd.read_csv("data/phase2_eval/eval_commonlid_11lang.csv")
    }
    for bname, bdf in benchmarks.items():
        print(f"Evaluation benchmark '{bname}': {len(bdf)} rows.")

    detailed_records = []
    summary_records = []

    # Include fastText from scratch results if available
    ft_json = "data/phase2_eval/fasttext_11lang_results.json"
    if os.path.exists(ft_json):
        print("\nLoading precomputed fastText (from scratch) results...")
        with open(ft_json, "r", encoding="utf-8") as f:
            ft_data = json.load(f)
        summary_row = {"Model": "fastText (from scratch)", "Architecture Paradigm": "Subword Embeddings"}
        for bname, key in [("FLORES+", "flores_plus"), ("WiLI-2018", "wili-2018"), ("CommonLID", "commonlid")]:
            if key in ft_data:
                res = ft_data[key]
                summary_row[bname] = res["macro_f1"]
                for c in CLASSES:
                    detailed_records.append({
                        "Model": "fastText (from scratch)",
                        "Architecture": "Subword Embeddings",
                        "Benchmark": bname,
                        "Language": c,
                        "F1": res["per_class_f1"].get(c, 0.0)
                    })
        summary_records.append(summary_row)

    # 3. Fit TF-IDF Feature Extractor for linear/probabilistic models
    print("\nFitting Character 2-4 gram TF-IDF Vectorizer (max_features=50,000)...")
    t0 = time.time()
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4), max_features=50000, sublinear_tf=True)
    X_train_tfidf = vectorizer.fit_transform(train_texts)
    print(f"TF-IDF fitted in {time.time()-t0:.2f}s, shape: {X_train_tfidf.shape}")

    # Pre-transform evaluation sets
    X_eval_tfidf = {bname: vectorizer.transform(bdf["text"].astype(str).tolist()) for bname, bdf in benchmarks.items()}

    # --- MODEL 1: Multinomial Naive Bayes ---
    print("\n" + "-" * 60)
    print("Training Model 1/7: Multinomial Naive Bayes (MNB)...")
    t0 = time.time()
    mnb = MultinomialNB(alpha=1.0)
    mnb.fit(X_train_tfidf, train_labels)
    print(f"MNB trained in {time.time()-t0:.2f}s.")

    mnb_summary = {"Model": "Multinomial NB", "Architecture Paradigm": "Probabilistic ML"}
    for bname, bdf in benchmarks.items():
        preds = mnb.predict(X_eval_tfidf[bname])
        acc, mf1, per_class = evaluate_predictions(bdf["label"].tolist(), preds)
        mnb_summary[bname] = mf1
        print(f"  {bname} => Acc: {acc:.4f}, Macro-F1: {mf1:.4f}")
        for c in CLASSES:
            detailed_records.append({
                "Model": "Multinomial NB",
                "Architecture": "Probabilistic ML",
                "Benchmark": bname,
                "Language": c,
                "F1": per_class[c]
            })
    summary_records.append(mnb_summary)

    # --- MODEL 2: Linear SVM ---
    print("\n" + "-" * 60)
    print("Training Model 2/7: Linear Support Vector Machine (Linear SVM)...")
    t0 = time.time()
    svm = LinearSVC(C=1.0, max_iter=2000, random_state=42)
    svm.fit(X_train_tfidf, train_labels)
    print(f"Linear SVM trained in {time.time()-t0:.2f}s.")

    svm_summary = {"Model": "Linear SVM", "Architecture Paradigm": "Margin Linear ML"}
    for bname, bdf in benchmarks.items():
        preds = svm.predict(X_eval_tfidf[bname])
        acc, mf1, per_class = evaluate_predictions(bdf["label"].tolist(), preds)
        svm_summary[bname] = mf1
        print(f"  {bname} => Acc: {acc:.4f}, Macro-F1: {mf1:.4f}")
        for c in CLASSES:
            detailed_records.append({
                "Model": "Linear SVM",
                "Architecture": "Margin Linear ML",
                "Benchmark": bname,
                "Language": c,
                "F1": per_class[c]
            })
    summary_records.append(svm_summary)

    # --- MODEL 3: Char n-gram + Logistic Regression ---
    print("\n" + "-" * 60)
    print("Training Model 3/7: Char n-gram + Logistic Regression...")
    t0 = time.time()
    lr = LogisticRegression(C=1.0, max_iter=500, solver="lbfgs", random_state=42)
    lr.fit(X_train_tfidf, train_labels)
    print(f"Logistic Regression trained in {time.time()-t0:.2f}s.")

    lr_summary = {"Model": "Char n-gram + LogReg", "Architecture Paradigm": "Frequency NLP Baseline"}
    for bname, bdf in benchmarks.items():
        preds = lr.predict(X_eval_tfidf[bname])
        acc, mf1, per_class = evaluate_predictions(bdf["label"].tolist(), preds)
        lr_summary[bname] = mf1
        print(f"  {bname} => Acc: {acc:.4f}, Macro-F1: {mf1:.4f}")
        for c in CLASSES:
            detailed_records.append({
                "Model": "Char n-gram + LogReg",
                "Architecture": "Frequency NLP Baseline",
                "Benchmark": bname,
                "Language": c,
                "F1": per_class[c]
            })
    summary_records.append(lr_summary)

    # --- MODEL 4: XGBoost ---
    print("\n" + "-" * 60)
    print("Training Model 4/7: XGBoost (Gradient Boosting on max_features=2500)...")
    t0 = time.time()
    xgb_vec = TfidfVectorizer(analyzer="char", ngram_range=(2, 4), max_features=2500, sublinear_tf=True)
    X_train_xgb = xgb_vec.fit_transform(train_texts)
    X_eval_xgb = {bname: xgb_vec.transform(bdf["text"].astype(str).tolist()) for bname, bdf in benchmarks.items()}

    xgb = XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        tree_method="hist",
        n_jobs=-1,
        random_state=42
    )
    xgb.fit(X_train_xgb, train_y_idx)
    print(f"XGBoost trained in {time.time()-t0:.2f}s.")

    xgb_summary = {"Model": "XGBoost", "Architecture Paradigm": "Gradient Tree Boosting"}
    for bname, bdf in benchmarks.items():
        preds_idx = xgb.predict(X_eval_xgb[bname])
        preds = [IDX_TO_CLASS[i] for i in preds_idx]
        acc, mf1, per_class = evaluate_predictions(bdf["label"].tolist(), preds)
        xgb_summary[bname] = mf1
        print(f"  {bname} => Acc: {acc:.4f}, Macro-F1: {mf1:.4f}")
        for c in CLASSES:
            detailed_records.append({
                "Model": "XGBoost",
                "Architecture": "Gradient Tree Boosting",
                "Benchmark": bname,
                "Language": c,
                "F1": per_class[c]
            })
    summary_records.append(xgb_summary)

    # --- Neural Preprocessing for Models 5 & 6 ---
    print("\nBuilding Character Vocabulary for Deep Learning Baselines...")
    char_vocab = CharVocabulary(max_len=200)
    char_vocab.build_vocab(train_texts)

    X_train_seq = char_vocab.transform(train_texts)
    train_ds = TextDataset(X_train_seq, train_y_idx)
    train_loader = DataLoader(train_ds, batch_size=256, shuffle=True)

    X_eval_seq = {bname: char_vocab.transform(bdf["text"].astype(str).tolist()) for bname, bdf in benchmarks.items()}

    # --- MODEL 5: Char-CNN ---
    print("\n" + "-" * 60)
    print("Training Model 5/7: Char-CNN (1D-CNN from scratch, 2 epochs)...")
    t0 = time.time()
    cnn = CharCNN(vocab_size=len(char_vocab.char2idx), emb_dim=64, num_classes=len(CLASSES)).to(device)
    cnn_opt = torch.optim.AdamW(cnn.parameters(), lr=0.002)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(2):
        cnn.train()
        total_loss = 0.0
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            cnn_opt.zero_grad()
            logits = cnn(batch_x)
            loss = criterion(logits, batch_y)
            loss.backward()
            cnn_opt.step()
            total_loss += loss.item()
        print(f"  Epoch {epoch+1}/2 complete, Avg Loss: {total_loss/len(train_loader):.4f}")
    print(f"Char-CNN trained in {time.time()-t0:.2f}s.")

    cnn_summary = {"Model": "Char-CNN", "Architecture Paradigm": "Deep Learning (1D-CNN)"}
    cnn.eval()
    with torch.no_grad():
        for bname, bdf in benchmarks.items():
            seqs = torch.tensor(X_eval_seq[bname], dtype=torch.long).to(device)
            loader = DataLoader(seqs, batch_size=512, shuffle=False)
            preds_idx = []
            for b_seq in loader:
                logits = cnn(b_seq)
                preds_idx.extend(logits.argmax(dim=1).cpu().numpy().tolist())
            preds = [IDX_TO_CLASS[i] for i in preds_idx]
            acc, mf1, per_class = evaluate_predictions(bdf["label"].tolist(), preds)
            cnn_summary[bname] = mf1
            print(f"  {bname} => Acc: {acc:.4f}, Macro-F1: {mf1:.4f}")
            for c in CLASSES:
                detailed_records.append({
                    "Model": "Char-CNN",
                    "Architecture": "Deep Learning (1D-CNN)",
                    "Benchmark": bname,
                    "Language": c,
                    "F1": per_class[c]
                })
    summary_records.append(cnn_summary)

    # --- MODEL 6: Char-BiGRU ---
    print("\n" + "-" * 60)
    print("Training Model 6/7: Char-BiGRU (Recurrent Neural Network, 1 epoch)...")
    t0 = time.time()
    bigru = CharBiGRU(vocab_size=len(char_vocab.char2idx), emb_dim=64, hidden_dim=128, num_classes=len(CLASSES)).to(device)
    bigru_opt = torch.optim.AdamW(bigru.parameters(), lr=0.002)

    bigru.train()
    total_loss = 0.0
    for batch_x, batch_y in train_loader:
        batch_x, batch_y = batch_x.to(device), batch_y.to(device)
        bigru_opt.zero_grad()
        logits = bigru(batch_x)
        loss = criterion(logits, batch_y)
        loss.backward()
        bigru_opt.step()
        total_loss += loss.item()
    print(f"Char-BiGRU trained in {time.time()-t0:.2f}s, Loss: {total_loss/len(train_loader):.4f}")

    bigru_summary = {"Model": "Char-BiGRU", "Architecture Paradigm": "Deep Learning (BiGRU)"}
    bigru.eval()
    with torch.no_grad():
        for bname, bdf in benchmarks.items():
            seqs = torch.tensor(X_eval_seq[bname], dtype=torch.long).to(device)
            loader = DataLoader(seqs, batch_size=512, shuffle=False)
            preds_idx = []
            for b_seq in loader:
                logits = bigru(b_seq)
                preds_idx.extend(logits.argmax(dim=1).cpu().numpy().tolist())
            preds = [IDX_TO_CLASS[i] for i in preds_idx]
            acc, mf1, per_class = evaluate_predictions(bdf["label"].tolist(), preds)
            bigru_summary[bname] = mf1
            print(f"  {bname} => Acc: {acc:.4f}, Macro-F1: {mf1:.4f}")
            for c in CLASSES:
                detailed_records.append({
                    "Model": "Char-BiGRU",
                    "Architecture": "Deep Learning (BiGRU)",
                    "Benchmark": bname,
                    "Language": c,
                    "F1": per_class[c]
                })
    summary_records.append(bigru_summary)

    # 4. Save and Output Results
    df_summary = pd.DataFrame(summary_records)
    summary_path = "results/phase2_baselines_11lang_summary.csv"
    df_summary.to_csv(summary_path, index=False)
    print("\n" + "=" * 80)
    print(f"Saved Phase 2 Baseline Summary to {summary_path}")
    print("=" * 80)
    print(df_summary.to_string(index=False))

    df_detailed = pd.DataFrame(detailed_records)
    detailed_path = "results/phase2_baselines_11lang_detailed.csv"
    df_detailed.to_csv(detailed_path, index=False)
    print(f"Saved Detailed Per-Class Results to {detailed_path}")

    # Build Comparison Table: 7 Baselines vs 6 SOTA Foundation Models
    sota_data = [
        {"Model": "XLM-R Base (LoRA + Mix)", "Architecture Paradigm": "Transformer (Foundation)", "FLORES+": 0.9267, "WiLI-2018": 0.8880, "CommonLID": 0.9737},
        {"Model": "ConLID (Head Ext.)", "Architecture Paradigm": "CNN-Transformer (Foundation)", "FLORES+": 0.9329, "WiLI-2018": 0.9688, "CommonLID": 0.9261},
        {"Model": "fastText LID-176 (Two-Stage)", "Architecture Paradigm": "Subwords (Foundation LID-176)", "FLORES+": 0.9276, "WiLI-2018": 0.9745, "CommonLID": 0.9645},
        {"Model": "GlotLID v3 (Vec Transfer)", "Architecture Paradigm": "Subwords (Foundation 2.1k)", "FLORES+": 0.9465, "WiLI-2018": 0.9570, "CommonLID": 0.9527},
        {"Model": "NLLB LID-218 (C++ Extend)", "Architecture Paradigm": "Subwords (Foundation LID-218)", "FLORES+": 0.9530, "WiLI-2018": 0.9675, "CommonLID": 0.9501},
        {"Model": "OpenLID-v2 (Two-Stage)", "Architecture Paradigm": "Subwords (Foundation OpenLID)", "FLORES+": 0.7759, "WiLI-2018": 0.7782, "CommonLID": 0.7913},
    ]
    df_sota = pd.DataFrame(sota_data)
    df_compare = pd.concat([df_summary, df_sota], ignore_index=True)
    compare_path = "results/phase2_baselines_vs_sota.csv"
    df_compare.to_csv(compare_path, index=False)
    print("\n" + "=" * 80)
    print(f"Saved Unified Comparison (7 Baselines vs 6 SOTA) to {compare_path}")
    print("=" * 80)
    print(df_compare.to_string(index=False))

if __name__ == "__main__":
    main()
