import os
import pandas as pd
import requests
from sklearn.model_selection import train_test_split
import fasttext
import numpy as np

def download_model(url, save_path):
    if not os.path.exists(save_path):
        print(f"Downloading {url} to {save_path}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download complete.")
    else:
        print(f"Model already exists at {save_path}.")

def dump_word_vectors(bin_model_path, vec_model_path):
    if os.path.exists(vec_model_path):
        print(f"Word vectors already dumped at {vec_model_path}.")
        return

    print(f"Loading {bin_model_path} to extract word vectors...")
    model = fasttext.load_model(bin_model_path)
    words = model.get_words()
    dim = model.get_dimension()
    
    print(f"Writing {len(words)} word vectors to {vec_model_path}...")
    with open(vec_model_path, 'w', encoding='utf-8') as f:
        f.write(f"{len(words)} {dim}\n")
        for word in words:
            vec = model.get_word_vector(word)
            vec_str = " ".join(map(str, vec))
            # fasttext words can sometimes contain spaces or newlines, though rare
            # safe to replace with something else or just skip
            safe_word = word.replace(' ', '_').replace('\n', '')
            f.write(f"{safe_word} {vec_str}\n")
    print("Done dumping word vectors.")

def prepare_data(csv_path, txt_path):
    print(f"Reading dataset from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    print(f"Formatting {csv_path} to FastText format...")
    formatted_data = []
    for index, row in df.iterrows():
        label = str(row['label']).strip()
        text = str(row['text']).replace('\n', ' ').replace('\r', ' ').strip()
        if text:
            formatted_data.append(f"__label__{label} {text}")
            
    print(f"Total samples: {len(formatted_data)}")
    
    print(f"Writing dataset to {txt_path}...")
    with open(txt_path, 'w', encoding='utf-8') as f:
        for line in formatted_data:
            f.write(f"{line}\n")
    return txt_path

def main():
    model_dir = "models"
    os.makedirs(model_dir, exist_ok=True)
    
    pretrained_model_url = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
    pretrained_model_path = os.path.join(model_dir, "lid.176.bin")
    pretrained_vec_path = os.path.join(model_dir, "lid.176.vec")
    
    download_model(pretrained_model_url, pretrained_model_path)
    dump_word_vectors(pretrained_model_path, pretrained_vec_path)
    
    data_dir = "data/Nadil"
    
    train_csv = os.path.join(data_dir, "train.csv")
    val_csv = os.path.join(data_dir, "val.csv")
    
    train_txt_path = os.path.join(data_dir, "train.txt")
    valid_txt_path = os.path.join(data_dir, "valid.txt")
    
    prepare_data(train_csv, train_txt_path)
    prepare_data(val_csv, valid_txt_path)
        
    finetuned_model_path = os.path.join(model_dir, "fasttext_finetuned.bin")
    
    print(f"Training new FastText classifier initialized with {pretrained_vec_path}...")
    # FastText 176 was trained with dim=16, epoch=1, lr=0.1, minn=2, maxn=4 (approx)
    model = fasttext.train_supervised(
        input=train_txt_path,
        pretrainedVectors=pretrained_vec_path,
        dim=16,          # Must match the dimension of pretrained vectors (lid.176 is dim 16)
        epoch=25,        # More epochs for fine-tuning on a small dataset
        lr=0.1,
        wordNgrams=1,
        minn=2,
        maxn=4,
        bucket=2000000,
        thread=4
    )
    
    print(f"Evaluating on {valid_txt_path}...")
    n, p, r = model.test(valid_txt_path)
    print(f"N: {n}")
    print(f"Precision: {p:.4f}")
    print(f"Recall: {r:.4f}")
    
    print(f"Saving fine-tuned model to {finetuned_model_path}...")
    model.save_model(finetuned_model_path)
    print("Done.")

if __name__ == "__main__":
    main()
