import os
import urllib.request

os.makedirs("data/raw/SiPaKosa", exist_ok=True)

mixed_url = "https://huggingface.co/datasets/RaniduG/SiPaKosa-Sent/resolve/main/data/mixed/train.csv"
sinhala_url = "https://huggingface.co/datasets/RaniduG/SiPaKosa-Sent/resolve/main/data/sinhala/train.csv"

print("Downloading mixed metadata...")
urllib.request.urlretrieve(mixed_url, "data/raw/SiPaKosa/sipakosa_mixed_metadata.csv")

print("Downloading sinhala metadata...")
urllib.request.urlretrieve(sinhala_url, "data/raw/SiPaKosa/sipakosa_sinhala_metadata.csv")

print("Download complete.")