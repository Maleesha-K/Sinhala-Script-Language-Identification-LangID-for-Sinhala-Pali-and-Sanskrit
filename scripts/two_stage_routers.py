"""
================================================================================
Unified Two-Stage Hierarchical Routers for 5 SOTA LangID Models
================================================================================
Implements Two-Stage Hierarchical Routing for:
  1. FastText LID-176
  2. OpenLID-v2
  3. NLLB LID-218
  4. GlotLID v3
  5. ConLID

Eliminates Catastrophic Forgetting:
  - Stage 1 (Frozen Stock Foundation Model): Routes global background languages
    directly with 0% degradation.
  - Stage 2 (Domain Specialist): If Stage 1 predicts Sinhala script ('si' / 'sin_Sinh'),
    routes to specialist for 3-way disambiguation: 'sinhala', 'pali', 'sanskrit'.
================================================================================
"""

import os
import sys
import re
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import fasttext
from huggingface_hub import hf_hub_download, snapshot_download

# Project root resolution
PROJ_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def fix_win_path(path: str) -> str:
    abs_path = os.path.abspath(path)
    if sys.platform == "win32" and not abs_path.startswith("\\\\?\\"):
        return "\\\\?\\" + abs_path
    return abs_path

# Standard 11 benchmark languages
ALL_BENCHMARK_LANGUAGES = [
    "sinhala", "pali", "sanskrit", "sanskrit_deva", "english", "tamil",
    "hindi", "bengali", "arabic", "french", "german"
]

# Mapping dictionary for BCP-47 / ISO codes to common language names
BCP47_TO_COMMON = {
    "eng_Latn": "english",
    "en": "english",
    "deu_Latn": "german",
    "de": "german",
    "fra_Latn": "french",
    "fr": "french",
    "tam_Taml": "tamil",
    "ta": "tamil",
    "hin_Deva": "hindi",
    "hi": "hindi",
    "ben_Beng": "bengali",
    "bn": "bengali",
    "arb_Arab": "arabic",
    "ar": "arabic",
    "san_Deva": "sanskrit_deva",
    "sa": "sanskrit_deva",
}

# Stage 2 label map: converts specialist labels to standard benchmark names
STAGE2_LABEL_MAP = {
    # Sinhala
    "sinhala": "sinhala",
    "sin_Sinh": "sinhala",
    "si": "sinhala",
    "sin": "sinhala",
    # Pali
    "pali": "pali",
    "pli_Sinh": "pali",
    "pli": "pali",
    "pi": "pali",
    # Sanskrit (Sinhala script)
    "sanskrit": "sanskrit",
    "san_Sinh": "sanskrit",
    "san": "sanskrit",
    # Sanskrit (Devanagari script)
    "sanskrit_deva": "sanskrit_deva",
    "san_Deva": "sanskrit_deva",
    "sa": "sanskrit_deva",
    # Fallback for undefined in Sinhala script
    "und_Sinh": "sinhala",
}


# ------------------------------------------------------------------------------
# Base Two-Stage Router Interface
# ------------------------------------------------------------------------------
class BaseTwoStageRouter(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def predict_stage1(self, text: str) -> str:
        """Runs stock foundation model to obtain raw predicted label."""
        pass

    @abstractmethod
    def is_sinhala_script(self, raw_stage1_label: str) -> bool:
        """Determines if the Stage 1 label corresponds to Sinhala script."""
        pass

    @abstractmethod
    def map_global_label(self, raw_stage1_label: str) -> str:
        """Maps non-Sinhala stock labels to common benchmark names."""
        pass

    @abstractmethod
    def predict_stage2(self, text: str) -> str:
        """Runs Stage 2 fine-tuned specialist to disambiguate Sinhala, Pali, Sanskrit."""
        pass

    def predict(self, text: str) -> str:
        """
        Two-stage inference:
        1. Query Stage 1 stock model.
        2. If non-Sinhala, return global language prediction immediately.
        3. If Sinhala script, query Stage 2 specialist for 3-way distinction.
        """
        clean_text = str(text).strip().replace("\n", " ")
        raw_s1 = self.predict_stage1(clean_text)
        
        if not self.is_sinhala_script(raw_s1):
            return self.map_global_label(raw_s1)
        
        # Route to Stage 2 Specialist
        return self.predict_stage2(clean_text)

    def predict_batch(self, texts: List[str]) -> List[str]:
        return [self.predict(t) for t in texts]


# ------------------------------------------------------------------------------
# 1. FastText LID-176 Two-Stage Router
# ------------------------------------------------------------------------------
class FastTextTwoStageRouter(BaseTwoStageRouter):
    def __init__(self, stock_path: Optional[str] = None, specialist_path: Optional[str] = None):
        super().__init__(name="FastText-LID-176-TwoStage")
        self.stock_path = stock_path or os.path.join(PROJ_ROOT, "models", "benchmark", "fastText", "lid.176.bin")
        if not os.path.exists(self.stock_path):
            alt = os.path.join(PROJ_ROOT, "models", "lid.176.bin")
            if os.path.exists(alt):
                self.stock_path = alt
        if not os.path.exists(self.stock_path):
            raise FileNotFoundError(f"FastText stock model not found at {self.stock_path}")
        
        self.specialist_path = specialist_path or os.path.join(PROJ_ROOT, "models", "fasttext_finetuned.bin")
        if not os.path.exists(self.specialist_path):
            alt = os.path.join(PROJ_ROOT, "data_pipeline", "models", "finetuned", "fastText_LID_176", "fasttext_lid_176_finetuned.bin")
            if os.path.exists(alt):
                self.specialist_path = alt
        if not os.path.exists(self.specialist_path):
            raise FileNotFoundError(f"FastText specialist model not found at {self.specialist_path}")

        print(f"[{self.name}] Loading Stock Model: {self.stock_path}")
        self.stock_model = fasttext.load_model(fix_win_path(self.stock_path))
        print(f"[{self.name}] Loading Specialist Model: {self.specialist_path}")
        self.specialist_model = fasttext.load_model(fix_win_path(self.specialist_path))

    def predict_stage1(self, text: str) -> str:
        p, _ = self.stock_model.predict(text, k=1)
        return p[0].replace("__label__", "")

    def is_sinhala_script(self, raw_stage1_label: str) -> bool:
        return raw_stage1_label == "si"

    def map_global_label(self, raw_stage1_label: str) -> str:
        return BCP47_TO_COMMON.get(raw_stage1_label, raw_stage1_label)

    def predict_stage2(self, text: str) -> str:
        p, _ = self.specialist_model.predict(text, k=1)
        lbl = p[0].replace("__label__", "").strip().lower()
        return STAGE2_LABEL_MAP.get(lbl, lbl)


# ------------------------------------------------------------------------------
# 2. OpenLID-v2 Two-Stage Router
# ------------------------------------------------------------------------------
class OpenLIDTwoStageRouter(BaseTwoStageRouter):
    def __init__(self, stock_path: Optional[str] = None, specialist_path: Optional[str] = None):
        super().__init__(name="OpenLID-v2-TwoStage")
        self.stock_path = stock_path or os.path.join(PROJ_ROOT, "models", "benchmark", "OpenLID", "model.bin")
        if not os.path.exists(self.stock_path):
            self.stock_path = hf_hub_download(repo_id="laurievb/OpenLID-v2", filename="model.bin")
        
        self.specialist_path = specialist_path or os.path.join(PROJ_ROOT, "models", "openlid_v2_finetuned.bin")
        if not os.path.exists(self.specialist_path):
            alt = os.path.join(PROJ_ROOT, "data_pipeline", "models", "openlid_v2_finetuned.bin")
            if os.path.exists(alt):
                self.specialist_path = alt
        if not os.path.exists(self.specialist_path):
            raise FileNotFoundError(f"OpenLID specialist model not found at {self.specialist_path}")

        print(f"[{self.name}] Loading Stock Model: {self.stock_path}")
        self.stock_model = fasttext.load_model(fix_win_path(self.stock_path))
        print(f"[{self.name}] Loading Specialist Model: {self.specialist_path}")
        self.specialist_model = fasttext.load_model(fix_win_path(self.specialist_path))

    def clean_text(self, text: str) -> str:
        text = str(text).strip().replace("\n", " ").lower()
        text = re.sub(r"[^\w\s]|\d", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def predict_stage1(self, text: str) -> str:
        cleaned = self.clean_text(text)
        p, _ = self.stock_model.predict(cleaned, k=1)
        return p[0].replace("__label__", "")

    def is_sinhala_script(self, raw_stage1_label: str) -> bool:
        return raw_stage1_label == "sin_Sinh"

    def map_global_label(self, raw_stage1_label: str) -> str:
        return BCP47_TO_COMMON.get(raw_stage1_label, raw_stage1_label)

    def predict_stage2(self, text: str) -> str:
        cleaned = self.clean_text(text)
        p, _ = self.specialist_model.predict(cleaned, k=1)
        lbl = p[0].replace("__label__", "").strip()
        return STAGE2_LABEL_MAP.get(lbl, lbl)


# ------------------------------------------------------------------------------
# 3. NLLB LID-218 / 220 Two-Stage Router
# ------------------------------------------------------------------------------
class NLLBLIDTwoStageRouter(BaseTwoStageRouter):
    def __init__(self, stock_path: Optional[str] = None, specialist_path: Optional[str] = None):
        super().__init__(name="NLLB-LID-218-TwoStage")
        self.stock_path = stock_path or os.path.join(PROJ_ROOT, "models", "benchmark", "NLLB", "model.bin")
        if not os.path.exists(self.stock_path):
            self.stock_path = hf_hub_download(repo_id="facebook/fasttext-language-identification", filename="model.bin")
        
        self.specialist_path = specialist_path or os.path.join(PROJ_ROOT, "models", "finetuned", "nllb_lid_220_finetuned.bin")
        if not os.path.exists(self.specialist_path):
            raise FileNotFoundError(f"NLLB specialist model not found at {self.specialist_path}")

        print(f"[{self.name}] Loading Stock Model: {self.stock_path}")
        self.stock_model = fasttext.load_model(fix_win_path(self.stock_path))
        print(f"[{self.name}] Loading Specialist Model: {self.specialist_path}")
        self.specialist_model = fasttext.load_model(fix_win_path(self.specialist_path))

    def predict_stage1(self, text: str) -> str:
        p, _ = self.stock_model.predict(text, k=1)
        return p[0].replace("__label__", "")

    def is_sinhala_script(self, raw_stage1_label: str) -> bool:
        return raw_stage1_label == "sin_Sinh"

    def map_global_label(self, raw_stage1_label: str) -> str:
        return BCP47_TO_COMMON.get(raw_stage1_label, raw_stage1_label)

    def predict_stage2(self, text: str) -> str:
        p, _ = self.specialist_model.predict(text, k=1)
        lbl = p[0].replace("__label__", "").strip()
        return STAGE2_LABEL_MAP.get(lbl, lbl)


# ------------------------------------------------------------------------------
# 4. GlotLID v3 Two-Stage Router
# ------------------------------------------------------------------------------
class GlotLIDTwoStageRouter(BaseTwoStageRouter):
    def __init__(self, stock_path: Optional[str] = None, specialist_path: Optional[str] = None):
        super().__init__(name="GlotLID-v3-TwoStage")
        self.stock_path = stock_path or os.path.join(PROJ_ROOT, "models", "benchmark", "GlotLID", "model.bin")
        if not os.path.exists(self.stock_path):
            self.stock_path = hf_hub_download(repo_id="cis-lmu/glotlid", filename="model.bin")
        
        self.specialist_path = specialist_path or os.path.join(PROJ_ROOT, "models", "finetuned", "glotlid_2104_finetuned.bin")
        if not os.path.exists(self.specialist_path):
            raise FileNotFoundError(f"GlotLID specialist model not found at {self.specialist_path}")

        print(f"[{self.name}] Loading Stock Model: {self.stock_path}")
        self.stock_model = fasttext.load_model(fix_win_path(self.stock_path))
        print(f"[{self.name}] Loading Specialist Model: {self.specialist_path}")
        self.specialist_model = fasttext.load_model(fix_win_path(self.specialist_path))

    def predict_stage1(self, text: str) -> str:
        p, _ = self.stock_model.predict(text, k=1)
        return p[0].replace("__label__", "")

    def is_sinhala_script(self, raw_stage1_label: str) -> bool:
        return raw_stage1_label in ["sin_Sinh", "und_Sinh"]

    def map_global_label(self, raw_stage1_label: str) -> str:
        return BCP47_TO_COMMON.get(raw_stage1_label, raw_stage1_label)

    def predict_stage2(self, text: str) -> str:
        p, _ = self.specialist_model.predict(text, k=1)
        lbl = p[0].replace("__label__", "").strip()
        return STAGE2_LABEL_MAP.get(lbl, lbl)


# ------------------------------------------------------------------------------
# 5. ConLID Two-Stage Router
# ------------------------------------------------------------------------------
class ConLIDTwoStageRouter(BaseTwoStageRouter):
    def __init__(self, repo_dir: Optional[str] = None, checkpoints_dir: Optional[str] = None, specialist_dir: Optional[str] = None):
        super().__init__(name="ConLID-TwoStage")
        self.repo_dir = repo_dir or os.path.join(PROJ_ROOT, "models", "benchmark", "ConLID", "repo")
        self.checkpoints_dir = checkpoints_dir or os.path.join(PROJ_ROOT, "models", "benchmark", "ConLID", "checkpoints")
        self.specialist_dir = specialist_dir or os.path.join(PROJ_ROOT, "models", "finetuned", "conlid")
        
        if not os.path.exists(os.path.join(self.repo_dir, "model.py")):
            raise FileNotFoundError(f"ConLID repository wrapper not found at {self.repo_dir}.")
        
        if not os.path.exists(self.checkpoints_dir):
            raise FileNotFoundError(f"ConLID stock checkpoints not found at {self.checkpoints_dir}.")

        if not os.path.exists(self.specialist_dir):
            raise FileNotFoundError(f"ConLID specialist checkpoints not found at {self.specialist_dir}.")

        # Dynamically import ConLID
        if self.repo_dir not in sys.path:
            sys.path.insert(0, self.repo_dir)
        
        from model import ConLID
        print(f"[{self.name}] Loading ConLID Stock Model: {self.checkpoints_dir}")
        self.stock_model = ConLID.from_pretrained(dir=self.checkpoints_dir)
        print(f"[{self.name}] Loading ConLID Specialist Model: {self.specialist_dir}")
        self.specialist_model = ConLID.from_pretrained(dir=self.specialist_dir)

    def predict_stage1(self, text: str) -> str:
        pred_result = self.stock_model.predict(text, k=1)
        return pred_result[0][0]

    def is_sinhala_script(self, raw_stage1_label: str) -> bool:
        return raw_stage1_label in ["sin_Sinh", "und_Sinh"]

    def map_global_label(self, raw_stage1_label: str) -> str:
        return BCP47_TO_COMMON.get(raw_stage1_label, raw_stage1_label)

    def predict_stage2(self, text: str) -> str:
        pred_result = self.specialist_model.predict(text, k=1)
        lbl = pred_result[0][0]
        return STAGE2_LABEL_MAP.get(lbl, lbl)


# ------------------------------------------------------------------------------
# 6. XLM-RoBERTa Two-Stage Router
# ------------------------------------------------------------------------------
class XLMRobertaTwoStageRouter(BaseTwoStageRouter):
    def __init__(self, stock_model_name: Optional[str] = None, specialist_dir: Optional[str] = None):
        super().__init__(name="XLM-RoBERTa-TwoStage")
        self.stock_model_name = stock_model_name or "papluca/xlm-roberta-base-language-detection"
        self.specialist_dir = specialist_dir or os.path.join(PROJ_ROOT, "models", "finetuned", "xlm_roberta")

        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer, AutoConfig
        from safetensors.torch import load_file
        from peft import PeftModel

        print(f"[{self.name}] Loading Stock Model: {self.stock_model_name}")
        self.stock_tokenizer = AutoTokenizer.from_pretrained(self.stock_model_name, local_files_only=True)
        self.stock_model = AutoModelForSequenceClassification.from_pretrained(self.stock_model_name, local_files_only=True)
        self.stock_model.eval()

        print(f"[{self.name}] Loading Specialist Model: {self.specialist_dir}")
        self.specialist_config = AutoConfig.from_pretrained(self.specialist_dir)
        self.specialist_tokenizer = AutoTokenizer.from_pretrained(self.specialist_dir)
        base_m = AutoModelForSequenceClassification.from_config(self.specialist_config)
        st = load_file(os.path.join(self.specialist_dir, "model.safetensors"))
        base_m.load_state_dict(st)
        self.specialist_model = PeftModel.from_pretrained(base_m, self.specialist_dir)
        self.specialist_model.eval()

    def contains_sinhala_script(self, text: str) -> bool:
        # Check Unicode range for Sinhala: \u0D80-\u0DFF
        return any('\u0D80' <= ch <= '\u0DFF' for ch in text)

    def is_sinhala_script(self, raw_stage1_label: str) -> bool:
        return raw_stage1_label in ["si", "sin", "sin_Sinh", "sinhala_script"]

    def predict_stage1(self, text: str) -> str:
        if self.contains_sinhala_script(text):
            return "sinhala_script"
        
        import torch
        inputs = self.stock_tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
        with torch.no_grad():
            outputs = self.stock_model(**inputs)
            pred_idx = torch.argmax(outputs.logits, dim=-1).item()
            return self.stock_model.config.id2label[pred_idx]

    def map_global_label(self, raw_stage1_label: str) -> str:
        return BCP47_TO_COMMON.get(raw_stage1_label, raw_stage1_label)

    def predict_stage2(self, text: str) -> str:
        import torch
        inputs = self.specialist_tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
        with torch.no_grad():
            outputs = self.specialist_model(**inputs)
            pred_idx = torch.argmax(outputs.logits, dim=-1).item()
            raw_lbl = self.specialist_config.id2label[pred_idx]
            return STAGE2_LABEL_MAP.get(raw_lbl, raw_lbl)


# ------------------------------------------------------------------------------
# Factory Function
# ------------------------------------------------------------------------------
def get_two_stage_router(model_name: str) -> BaseTwoStageRouter:
    name = model_name.lower().replace("-", "").replace("_", "")
    if "fasttext" in name:
        return FastTextTwoStageRouter()
    elif "openlid" in name:
        return OpenLIDTwoStageRouter()
    elif "nllb" in name:
        return NLLBLIDTwoStageRouter()
    elif "glotlid" in name:
        return GlotLIDTwoStageRouter()
    elif "conlid" in name:
        return ConLIDTwoStageRouter()
    elif "xlm" in name or "roberta" in name:
        return XLMRobertaTwoStageRouter()
    else:
        raise ValueError(f"Unknown model name: {model_name}. Choose from: fasttext, openlid, nllb, glotlid, conlid, xlmr.")
