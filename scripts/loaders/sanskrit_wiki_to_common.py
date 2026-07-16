import bz2
import csv
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from aksharamukha import transliterate

# Make sure we can import common.py
sys.path.insert(0, str(Path(__file__).parent))
from common import SCHEMA

REPO = Path(__file__).resolve().parents[2]
PROC = REPO / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

OUT = PROC / "sanskrit_wiki_common.csv"
DUMP_URL = "https://dumps.wikimedia.org/sawiki/latest/sawiki-latest-pages-articles.xml.bz2"
DUMP_FILE = REPO / "data" / "raw" / "sawiki-latest-pages-articles.xml.bz2"

TARGET_SENTENCES = 35000

def download_dump():
    (REPO / "data" / "raw").mkdir(parents=True, exist_ok=True)
    if not DUMP_FILE.exists():
        print(f"Downloading Sanskrit Wikipedia dump (approx 30MB) from {DUMP_URL}...")
        req = urllib.request.Request(DUMP_URL, headers={'User-Agent': 'LangID-Bot/1.0'})
        with urllib.request.urlopen(req) as response, open(DUMP_FILE, 'wb') as out_file:
            out_file.write(response.read())
        print("Download complete.")

def clean_text(text):
    # Remove wiki markup roughly
    text = re.sub(r'\{\{.*?\}\}', '', text, flags=re.DOTALL)
    text = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', text)
    text = re.sub(r'<ref.*?</ref>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'==.*?==', '', text)
    text = re.sub(r'\[http.*?\]', '', text)
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def split_into_sentences(text):
    # Sanskrit sentences typically end with a danda (।) or double danda (॥)
    sentences = re.split(r'[।॥]', text)
    return [s.strip() for s in sentences if s.strip()]

def process_dump():
    print("Processing dump and transliterating...")
    
    with open(OUT, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(SCHEMA)
        
        count = 0
        
        # We use iterparse to stream the XML without loading it all in memory
        with bz2.open(DUMP_FILE, 'rb') as bz2_file:
            context = ET.iterparse(bz2_file, events=('end',))
            for event, elem in context:
                # The tag name usually has a namespace, e.g. {http://www.mediawiki.org/xml/export-0.11/}page
                if elem.tag.endswith('page'):
                    ns = elem.tag.split('}')[0] + '}' if '}' in elem.tag else ''
                    
                    title_elem = elem.find(f'{ns}title')
                    revision_elem = elem.find(f'{ns}revision')
                    
                    if title_elem is not None and revision_elem is not None:
                        text_elem = revision_elem.find(f'{ns}text')
                        if text_elem is not None and text_elem.text:
                            title = title_elem.text
                            raw_text = text_elem.text
                            
                            cleaned = clean_text(raw_text)
                            sentences = split_into_sentences(cleaned)
                            
                            for i, s in enumerate(sentences):
                                if len(s.split()) < 3 or len(s) < 15:
                                    continue
                                latin_chars = sum(1 for c in s if 'a' <= c.lower() <= 'z')
                                if latin_chars > len(s) * 0.1:
                                    continue
                                
                                try:
                                    sin_text = transliterate.process('Devanagari', 'Sinhala', s)
                                except Exception:
                                    continue
                                
                                row_id = f"wiki_sa_{count:06d}"
                                group_id = f"wiki_{title}"
                                
                                writer.writerow([
                                    row_id,
                                    sin_text,
                                    "sanskrit",
                                    "wiki_sa",
                                    "wiki",
                                    group_id,
                                    True,
                                    ""
                                ])
                                
                                count += 1
                                if count % 5000 == 0:
                                    print(f"  Extracted {count} sentences...")
                                    
                                if count >= TARGET_SENTENCES:
                                    elem.clear()
                                    return
                    
                    elem.clear()

if __name__ == "__main__":
    download_dump()
    process_dump()
    print("Done generating sanskrit_wiki_common.csv!")
