import sys
import os
import json
import glob
import urllib.request
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, f1_score
import fasttext

def fix_win_path(path):
    abs_path = os.path.abspath(path)
    if sys.platform == "win32" and not abs_path.startswith("\\\\?\\"):
        return "\\\\?\\" + abs_path
    return abs_path

# Auto-resolve the project root if running manually
if not os.path.exists("Makefile") and os.path.exists("../../Makefile"):
    os.chdir("../../")

input_file = fix_win_path('datasets/finetuning/train.csv')
if not os.path.exists(input_file):
    input_file = fix_win_path('../data/Nadil/train.csv')
if not os.path.exists(input_file):
    input_file = fix_win_path('data/Nadil/train.csv')

benchmark_dir = fix_win_path('datasets/preprocessed')
output_dir = fix_win_path('models/finetuned/fastText_LID_176')

MODEL_NAME = "fastText LID-176"
MODEL_ID = "fasttext_lid_176"

MODEL_URL = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
base_model_dir = fix_win_path("models/benchmark/fastText")
base_model_path = os.path.join(base_model_dir, "lid.176.bin")

if not os.path.exists(base_model_path):
    print("Downloading fastText LID-176 base model (~126MB)...")
    os.makedirs(base_model_dir, exist_ok=True)
    urllib.request.urlretrieve(MODEL_URL, base_model_path)

print(f"Loading base fastText LID-176 model from {base_model_path}...")
base_model = fasttext.load_model(base_model_path)

vec_file_path = os.path.join(base_model_dir, "lid.176.vec")
if not os.path.exists(vec_file_path):
    print("Extracting pre-trained word vectors to .vec format...")
    words = base_model.get_words()
    dim = base_model.get_dimension()
    with open(vec_file_path, "w", encoding="utf-8") as f:
        f.write(f"{len(words)} {dim}\n")
        for word in words:
            v_str = " ".join(map(str, base_model.get_word_vector(word)))
            f.write(f"{word} {v_str}\n")
    print(f"Extracted {len(words)} vectors into {vec_file_path}")

print(f"Loading finetuning dataset from {input_file}...")
df = pd.read_csv(input_file)
print(f"Loaded {len(df)} rows.")

def format_text(text):
    return str(text).replace("\n", " ").strip()

df["clean_text"] = df["text"].apply(format_text)
df["ft_line"] = "__label__" + df["label"].astype(str) + " " + df["clean_text"]

train_df, val_df = train_test_split(df, test_size=0.1, random_state=42, stratify=df["label"])

os.makedirs(output_dir, exist_ok=True)
train_ft_file = os.path.join(output_dir, "train_formatted.txt")
val_ft_file = os.path.join(output_dir, "val_formatted.txt")

base_labels = base_model.get_labels()
dummy_label_lines = [f"{lbl} ." for lbl in base_labels]
all_train_lines = dummy_label_lines + train_df["ft_line"].tolist()

with open(train_ft_file, "w", encoding="utf-8") as f:
    f.write("\n".join(all_train_lines) + "\n")

with open(val_ft_file, "w", encoding="utf-8") as f:
    f.write("\n".join(val_df["ft_line"].tolist()) + "\n")

print(f"Saved {len(dummy_label_lines)} base label declarations + {len(train_df)} training samples to {train_ft_file}")
print(f"Saved {len(val_df)} validation samples to {val_ft_file}")

save_model_path = os.path.join(output_dir, f"{MODEL_ID}_finetuned.bin")

if os.path.exists(save_model_path):
    print(f"Loading existing fine-tuned model from {save_model_path}...")
    finetuned_model = fasttext.load_model(save_model_path)
else:
    print(f"Starting fine-tuning for {MODEL_NAME}...")
    finetuned_model = fasttext.train_supervised(
        input=train_ft_file,
        pretrainedVectors=vec_file_path,
        dim=base_model.get_dimension(),
        epoch=25,
        lr=0.5,
        wordNgrams=2,
        loss="softmax"
    )
    finetuned_model.save_model(save_model_path)
    print(f"Fine-tuned model successfully saved to {save_model_path}")

val_texts = val_df["clean_text"].tolist()
val_true = val_df["label"].astype(str).tolist()

print(f"Evaluating fine-tuned {MODEL_NAME} on {len(val_texts)} validation samples...")
preds, _ = finetuned_model.predict(val_texts, k=1)
val_pred = [p[0].replace("__label__", "") for p in preds]

acc = accuracy_score(val_true, val_pred)
macro_f1 = f1_score(val_true, val_pred, average="macro")

print("\n" + "=" * 48)
print(f"VALIDATION FINE-TUNING RESULTS ({MODEL_NAME})")
print("=" * 48)
print(f"Accuracy:  {acc * 100:.2f}%")
print(f"Macro F1:  {macro_f1 * 100:.2f}%")
print("=" * 48)
print("\nPer-language breakdown:\n")
print(classification_report(val_true, val_pred, digits=4, zero_division=0))

print(f"Evaluating fine-tuned {MODEL_NAME} on hybrid benchmark datasets in {benchmark_dir}...")

ALL_BENCHMARK_LANGUAGES = [
    "sinhala", "pali", "sanskrit", "sanskrit_deva", "english", "tamil",
    "hindi", "bengali", "arabic", "french", "german"
]

LABEL_MAPPING_ALL = {
    "sin": "sinhala", "sin_Sinh": "sinhala", "sinhala": "sinhala", "si": "sinhala",
    "pli": "pali", "pli_Sinh": "pali", "pli_Latn": "pali", "pali": "pali", "pi": "pali",
    "sanskrit": "sanskrit", "san_Sinh": "sanskrit",
    "san_Deva": "sanskrit_deva", "sa": "sanskrit_deva",
    "eng": "english", "eng_Latn": "english", "english": "english", "en": "english",
    "tam": "tamil", "tam_Taml": "tamil", "tamil": "tamil", "ta": "tamil",
    "hin": "hindi", "hin_Deva": "hindi", "hindi": "hindi", "hi": "hindi",
    "ben": "bengali", "ben_Beng": "bengali", "bengali": "bengali", "bn": "bengali",
    "arb": "arabic", "arb_Arab": "arabic", "arabic": "arabic", "ar": "arabic",
    "fra": "french", "fra_Latn": "french", "french": "french", "fr": "french",
    "deu": "german", "deu_Latn": "german", "german": "german", "de": "german"
}

def map_all_label(row):
    lbl = str(row.get("label", "")).strip()
    src = str(row.get("source", "")).strip()
    if lbl == "san":
        if src in ["DCS", "SansinNT", "SiDiaC-v2", "Nadil"]:
            return "sanskrit"
        else:
            return "sanskrit_deva"
    return LABEL_MAPPING_ALL.get(lbl)

def load_all_languages_dataset(file_path):
    records = []
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            row = json.loads(line)
            mapped_label = map_all_label(row)
            if mapped_label:
                row["target_label"] = mapped_label
                records.append(row)
    return pd.DataFrame(records)

benchmark_files = ['flores_plus_integrated.jsonl', 'commonlid_integrated.jsonl', 'wili-2018_integrated.jsonl']
results_dir = fix_win_path(os.path.join("datasets", "benchmark_results"))
os.makedirs(results_dir, exist_ok=True)

for fname in benchmark_files:
    file_path = fix_win_path(os.path.join("datasets/preprocessed", fname))
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found.")
        continue
    
    dataset_name = os.path.splitext(fname)[0]
    df_all = load_all_languages_dataset(file_path)
    if df_all.empty:
        print(f"No matching languages found in {dataset_name}.")
        continue
    
    texts = df_all["text"].apply(format_text).tolist()
    print(f"\nEvaluating {len(texts)} samples across ALL benchmark languages from {dataset_name}...")
    preds, _ = finetuned_model.predict(texts, k=1)
    
    results = df_all[["text", "label", "source"]].copy()
    results["true_label"] = df_all["target_label"]
    results["predicted_label"] = [p[0].replace("__label__", "") for p in preds]
    
    acc_all = accuracy_score(results["true_label"], results["predicted_label"])
    macro_f1_all = f1_score(
        results["true_label"], results["predicted_label"],
        average="macro", labels=ALL_BENCHMARK_LANGUAGES, zero_division=0
    )
    
    print("=" * 65)
    print(f"FINE-TUNED BENCHMARK RESULTS ({MODEL_NAME} Finetuned on train.csv - Evaluated on {dataset_name})")
    print("=" * 65)
    print(f"Accuracy:  {acc_all * 100:.2f}%")
    print(f"Macro F1:  {macro_f1_all * 100:.2f}%")
    print("=" * 65)
    print("\nPer-language breakdown:\n")
    print(classification_report(
        results["true_label"], results["predicted_label"],
        labels=ALL_BENCHMARK_LANGUAGES, digits=4, zero_division=0
    ))
    
    out_csv = fix_win_path(os.path.join(results_dir, f"{MODEL_ID}_finetuned_all_langs_{dataset_name}.csv"))
    results.to_csv(out_csv, index=False)
    print(f"Saved all-languages benchmark predictions to {out_csv}")

print("\n" + "=" * 50)
print(f"FINE-TUNING & BENCHMARKING COMPLETE FOR {MODEL_NAME}")
print(f"Fine-tuned model saved to: {save_model_path}")
print("=" * 50)
