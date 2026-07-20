import requests
import json
import pandas as pd
import time
import os
import re

OUTPUT_CSV = r"data\processed\pali_suttacentral_common.csv"
MN_API_URL = "https://api.github.com/repos/suttacentral/bilara-data/contents/root/pli/ms/sutta/mn"
AKSHARA_API_URL = "https://aksharamukha-plugin.appspot.com/api/public"

def transliterate_chunk(text_chunk):
    """Transliterates a chunk of text using the Aksharamukha API."""
    try:
        response = requests.post(
            AKSHARA_API_URL, 
            data={"source": "IAST", "target": "Sinhala", "text": text_chunk},
            timeout=30
        )
        if response.status_code == 200:
            return response.text
        else:
            print(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def main():
    print("Fetching file list from SuttaCentral GitHub (Majjhima Nikaya)...")
    response = requests.get(MN_API_URL)
    if response.status_code != 200:
        print("Failed to fetch file list.")
        return
        
    files = response.json()
    print(f"Found {len(files)} files.")
    
    # We will limit to first 30 files for a reasonable execution time and to get ~3000+ sentences.
    # The MN has 152 files, which is massive. 30 files will be plenty to balance against the 3328 Pali sentences we currently have.
    files = files[:30]
    
    dataset_rows = []
    
    for i, file_info in enumerate(files):
        filename = file_info['name']
        group_id = filename.split('_')[0] # e.g. 'mn1'
        download_url = file_info['download_url']
        
        print(f"Processing {i+1}/{len(files)}: {filename}")
        
        file_resp = requests.get(download_url)
        if file_resp.status_code != 200:
            print(f"Failed to download {filename}")
            continue
            
        data = file_resp.json()
        
        # Filter and clean sentences
        sentences = []
        keys = []
        for k, v in data.items():
            text = v.strip()
            # Filter out purely numeric segments or very short fragments
            if text and not re.match(r'^[\d\.\s\-\:]+$', text) and len(text) > 10:
                sentences.append(text)
                keys.append(k)
        
        if not sentences:
            continue
            
        # Transliterate in batches of 50 sentences to avoid payload limits
        batch_size = 50
        for j in range(0, len(sentences), batch_size):
            batch = sentences[j:j+batch_size]
            chunk_text = "\n\n".join(batch)
            
            transliterated = transliterate_chunk(chunk_text)
            
            if transliterated:
                transliterated_lines = transliterated.split("\n\n")
                if len(transliterated_lines) == len(batch):
                    for line in transliterated_lines:
                        dataset_rows.append({
                            'group_id': group_id,
                            'label': 'pali',
                            'text': line.strip()
                        })
                else:
                    print(f"Warning: Batch length mismatch in {filename}")
            
            time.sleep(1) # Polite delay
            
    print(f"Total sentences extracted and transliterated: {len(dataset_rows)}")
    
    df = pd.DataFrame(dataset_rows)
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"Saved dataset to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
