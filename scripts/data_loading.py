from datasets import load_dataset
import os

ds_mixed = load_dataset("RaniduG/SiPaKosa-Sent", "mixed_metadata")
ds_sinhala = load_dataset("RaniduG/SiPaKosa-Sent", "sinhala_metadata")

print(ds_mixed)
print(ds_sinhala)

os.makedirs("data/raw/SiPaKosa", exist_ok=True)

ds_mixed["train"].to_csv("data/raw/SiPaKosa/sipakosa_mixed_metadata.csv")
ds_sinhala["train"].to_csv("data/raw/SiPaKosa/sipakosa_sinhala_metadata.csv")