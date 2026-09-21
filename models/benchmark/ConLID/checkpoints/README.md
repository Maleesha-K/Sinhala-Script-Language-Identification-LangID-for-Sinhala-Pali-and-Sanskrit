---
datasets:
- cis-lmu/glotlid-corpus
pipeline_tag: text-classification
metrics:
- f1
---

## Description
**ConLID**: Language Identification model that supports more than 2000 languages (three-letter ISO codes with script). For the list of all supported languages please refer to [labels.json](https://huggingface.co/Jakh0103/lid/blob/main/labels.json).

Repository: [GitHub](https://github.com/epfl-nlp/language-identification) \
Paper: [Paper](https://huggingface.co/papers/2506.15304)

## Usage
**Setup**
```bash
git clone https://github.com/epfl-nlp/ConLID.git
pip install -r requirements.txt
```

**Download the model**
```python
from huggingface_hub import snapshot_download

snapshot_download(repo_id="Jakh0103/lid", local_dir="checkpoint")
```

**Use the model**
```python
from model import LID
model = LID.from_pretrained(dir='checkpoint')

# print the supported labels
print(model.get_labels())
## ['aai_Latn', 'aak_Latn', 'aau_Latn', 'aaz_Latn', 'aba_Latn', ...]

# prediction
model.predict("The cat climbed onto the roof to enjoy the warm sunlight peacefully!")
# (['eng_Latn'], [0.970989465713501])

model.predict("The cat climbed onto the roof to enjoy the warm sunlight peacefully!", k=3)
## (['eng_Latn', 'sco_Latn', 'jam_Latn'], [0.970989465713501, 0.006496887654066086, 0.00487488554790616])
```