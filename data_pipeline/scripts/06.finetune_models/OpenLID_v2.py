import sys
import os
import re
import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, f1_score
import fasttext
from huggingface_hub import hf_hub_download

def fix_win_path(path):
    abs_path = os.path.abspath(path)
    if sys.platform == "win32" and not abs_path.startswith("\\\\?\\"):
        return "\\\\?\\" + abs_path
    return abs_path

# Ensure working directory is project root
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
os.chdir(proj_root)

input_file = os.path.join(proj_root, 'data', 'Nadil', 'train.csv')
if not os.path.exists(input_file):
    input_file = os.path.join(proj_root, 'data_pipeline', 'datasets', 'finetuning', 'train.csv')

benchmark_dir = os.path.join(proj_root, 'data_pipeline', 'datasets', 'preprocessed')
output_dir = os.path.join(proj_root, 'data_pipeline', 'models', 'finetuned', 'OpenLID_v2')

MODEL_NAME = "OpenLID-v2"
MODEL_ID = "openlid_v2"

print("Downloading OpenLID-v2 base model from Hugging Face...")
base_model_path = hf_hub_download(repo_id="laurievb/OpenLID-v2", filename="model.bin")
base_model_dir = os.path.dirname(base_model_path)

print(f"Loading base OpenLID-v2 model from {base_model_path}...")
base_model = fasttext.load_model(base_model_path)

vec_file_path = os.path.join(base_model_dir, "openlid_v2.vec")
if not os.path.exists(vec_file_path):
    print("Extracting pre-trained OpenLID-v2 word vectors to .vec format...")
    words = base_model.get_words()
    dim = base_model.get_dimension()
    with open(vec_file_path, "w", encoding="utf-8") as f:
        f.write(f"{len(words)} {dim}\n")
        for word in words:
            v_str = " ".join(map(str, base_model.get_word_vector(word)))
            f.write(f"{word} {v_str}\n")
    print(f"Extracted {len(words)} vectors into {vec_file_path}")

print(f"Loading finetuning dataset from {input_file}...")
df = pd.read_csv(fix_win_path(input_file))
print(f"Loaded {len(df)} rows.")

def clean_for_openlid(text):
    text = str(text).strip().replace("\n", " ").lower()
    text = re.sub(r"[^\w\s]|\d", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

df["clean_text"] = df["text"].apply(clean_for_openlid)
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

save_model_path = fix_win_path(os.path.join(proj_root, "data_pipeline", "models", "openlid_v2_finetuned.bin"))

if os.path.exists(save_model_path):
    print(f"Loading existing fine-tuned OpenLID-v2 model from {save_model_path}...")
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
    print(f"Fine-tuned OpenLID-v2 model successfully saved to {save_model_path}")

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
    with open(fix_win_path(file_path), encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            row = json.loads(line)
            mapped_label = map_all_label(row)
            if mapped_label:
                row["target_label"] = mapped_label
                records.append(row)
    return pd.DataFrame(records)

benchmark_files = ['flores_plus.jsonl', 'commonlid.jsonl', 'wili-2018.jsonl']
results_dir = os.path.join(proj_root, "data_pipeline", "datasets", "benchmark_results")
os.makedirs(results_dir, exist_ok=True)

for fname in benchmark_files:
    file_path = os.path.join(benchmark_dir, fname)
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found.")
        continue
    
    dataset_name = os.path.splitext(fname)[0]
    df_all = load_all_languages_dataset(file_path)
    if df_all.empty:
        print(f"No matching languages found in {dataset_name}.")
        continue
    
    texts = df_all["text"].apply(clean_for_openlid).tolist()
    print(f"\nEvaluating fine-tuned OpenLID-v2 on {len(texts)} samples across ALL benchmark languages from {dataset_name}...")
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
    
    out_csv = fix_win_path(os.path.join(results_dir, f"openlid_v2_finetuned_all_langs_{dataset_name}.csv"))
    results.to_csv(out_csv, index=False)
    print(f"Saved all-languages benchmark predictions to {out_csv}")

print("\n" + "=" * 50)
print(f"FINE-TUNING & BENCHMARKING COMPLETE FOR {MODEL_NAME}")
print(f"Fine-tuned model saved to: {save_model_path}")
print("=" * 50)
