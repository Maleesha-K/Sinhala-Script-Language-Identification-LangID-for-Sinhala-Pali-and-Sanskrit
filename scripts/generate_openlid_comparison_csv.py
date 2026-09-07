import os
import sys
import pandas as pd

def fix_win_path(path):
    abs_path = os.path.abspath(path)
    if sys.platform == "win32" and not abs_path.startswith("\\\\?\\"):
        return "\\\\?\\" + abs_path
    return abs_path

# Paths
master_csv_path = "Comparison Tables - Final copy.csv"
out_csv_path = "Comparison Tables - OpenLID Finetuned.csv"
benchmark_results_dir = os.path.join("data_pipeline", "datasets", "benchmark_results")

# Load master template
df = pd.read_csv(master_csv_path)

benchmark_cols = {
    "flores_plus": {
        "Sinhala-Sinh": 1, "Pali-Sinh": 2, "Sanskrit-Sinh": 3, "Sanskrit-Deva": 4,
        "English-Latn": 5, "Tamil-Taml": 6, "Hindi-Deva": 7, "Bengali-Beng": 8,
        "Arabic-Arab": 9, "French-Latn": 10, "German-Latn": 11
    },
    "commonlid": {
        "Sinhala-Sinh": 14, "Pali-Sinh": 15, "Sanskrit-Sinh": 16, "Sanskrit-Deva": 17,
        "English-Latn": 18, "Tamil-Taml": 19, "Hindi-Deva": 20, "Bengali-Beng": 21,
        "Arabic-Arab": 22, "French-Latn": 23, "German-Latn": 24
    },
    "wili-2018": {
        "Sinhala-Sinh": 27, "Pali-Sinh": 28, "Sanskrit-Sinh": 29, "Sanskrit-Deva": 30,
        "English-Latn": 31, "Tamil-Taml": 32, "Hindi-Deva": 33, "Bengali-Beng": 34,
        "Arabic-Arab": 35, "French-Latn": 36, "German-Latn": 37
    }
}

target_lang_keys = {
    "Sinhala-Sinh": "sin_Sinh",
    "Pali-Sinh": "pli_Sinh",
    "Sanskrit-Sinh": "san_Sinh",
    "Sanskrit-Deva": "san_Deva",
    "English-Latn": "eng_Latn",
    "Tamil-Taml": "tam_Taml",
    "Hindi-Deva": "hin_Deva",
    "Bengali-Beng": "ben_Beng",
    "Arabic-Arab": "arb_Arab",
    "French-Latn": "fra_Latn",
    "German-Latn": "deu_Latn"
}

finetuned_lang_keys = {
    "Sinhala-Sinh": "sinhala",
    "Pali-Sinh": "pali",
    "Sanskrit-Sinh": "sanskrit",
    "Sanskrit-Deva": "sanskrit_deva",
    "English-Latn": "english",
    "Tamil-Taml": "tamil",
    "Hindi-Deva": "hindi",
    "Bengali-Beng": "bengali",
    "Arabic-Arab": "arabic",
    "French-Latn": "french",
    "German-Latn": "german"
}

# 1. Zero-shot OpenLID-v2
row_idx_zero = None
for i in range(len(df)):
    if str(df.iloc[i, 0]).strip() == "OpenLID-v2":
        row_idx_zero = i
        break

# 2. Fine-tuned / Two-Stage OpenLID-v2
row_idx_ft = None
for i in range(13, len(df)):
    if str(df.iloc[i, 0]).strip() == "OpenLID-v2":
        row_idx_ft = i
        break

print(f"Zero-shot row index: {row_idx_zero}, Fine-tuned row index: {row_idx_ft}")

if row_idx_zero is not None:
    for bname, col_map in benchmark_cols.items():
        pred_path = fix_win_path(os.path.join(benchmark_results_dir, f"openlid_v2_{bname}.csv"))
        if os.path.exists(pred_path):
            res_df = pd.read_csv(pred_path)
            for lang_name, col_idx in col_map.items():
                true_key = target_lang_keys[lang_name]
                sub = res_df[res_df["true_label"] == true_key]
                if not sub.empty:
                    tp = len(res_df[(res_df["true_label"] == true_key) & (res_df["predicted_label"] == true_key)])
                    fp = len(res_df[(res_df["true_label"] != true_key) & (res_df["predicted_label"] == true_key)])
                    fn = len(res_df[(res_df["true_label"] == true_key) & (res_df["predicted_label"] != true_key)])
                    prec = tp / (tp + fp) if (tp + fp) > 0 else 0
                    rec = tp / (tp + fn) if (tp + fn) > 0 else 0
                    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
                    df.iloc[row_idx_zero, col_idx] = f"{f1:.4f}"

if row_idx_ft is not None:
    for bname, col_map in benchmark_cols.items():
        # Prefer two-stage predictions if available
        pred_path = fix_win_path(os.path.join(benchmark_results_dir, f"openlid_v2_twostage_all_langs_{bname}.csv"))
        if not os.path.exists(pred_path):
            pred_path = fix_win_path(os.path.join(benchmark_results_dir, f"openlid_v2_finetuned_all_langs_{bname}.csv"))
            
        if os.path.exists(pred_path):
            res_df = pd.read_csv(pred_path)
            for lang_name, col_idx in col_map.items():
                true_key = finetuned_lang_keys[lang_name]
                sub = res_df[res_df["true_label"] == true_key]
                if not sub.empty:
                    tp = len(res_df[(res_df["true_label"] == true_key) & (res_df["predicted_label"] == true_key)])
                    fp = len(res_df[(res_df["true_label"] != true_key) & (res_df["predicted_label"] == true_key)])
                    fn = len(res_df[(res_df["true_label"] == true_key) & (res_df["predicted_label"] != true_key)])
                    prec = tp / (tp + fp) if (tp + fp) > 0 else 0
                    rec = tp / (tp + fn) if (tp + fn) > 0 else 0
                    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
                    df.iloc[row_idx_ft, col_idx] = f"{f1:.4f}"

df.to_csv(out_csv_path, index=False)
print(f"Successfully generated populated comparison table CSV at: {out_csv_path}")
