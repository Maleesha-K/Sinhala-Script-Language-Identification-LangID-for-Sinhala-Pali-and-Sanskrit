output_dir = 'datasets/raw_download/wili-2018'

import os
# Auto-resolve the project root if running manually
if not os.path.exists("Makefile") and os.path.exists("../../Makefile"):
    os.chdir("../../")

import os
import urllib.request
import zipfile

print(f"Downloading WiLI-2018 dataset to {output_dir}...")
os.makedirs(output_dir, exist_ok=True)

url = "https://zenodo.org/record/841984/files/wili-2018.zip"
zip_path = os.path.join(output_dir, "wili-2018.zip")

urllib.request.urlretrieve(url, zip_path)

with zipfile.ZipFile(zip_path, "r") as zf:
    zf.extractall(output_dir)

os.remove(zip_path)

print(f"Downloaded and extracted WiLI-2018 dataset to {output_dir}")

