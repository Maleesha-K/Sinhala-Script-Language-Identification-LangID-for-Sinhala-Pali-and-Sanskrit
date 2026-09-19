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

# ------------------------------------------------------------------------------
# Base Two-Stage Router Interface
# ------------------------------------------------------------------------------
class BaseTwoStageRouter(ABC):
    def __init__(self, name: str, specialist_path: Optional[str] = None):
        self.name = name
        self.specialist_path = specialist_path or os.path.join(PROJ_ROOT, "models", "fasttext_finetuned.bin")
        self.specialist_model = None
        self._load_specialist()

    def _load_specialist(self):
        if not os.path.exists(self.specialist_path):
            alt_path = os.path.join(PROJ_ROOT, "data_pipeline", "models", "finetuned", "fastText_LID_176", "fasttext_lid_176_finetuned.bin")
            if os.path.exists(alt_path):
                self.specialist_path = alt_path
        if os.path.exists(self.specialist_path):
            self.specialist_model = fasttext.load_model(fix_win_path(self.specialist_path))
        else:
            raise FileNotFoundError(f"Specialist model not found at: {self.specialist_path}")

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
        p2, _ = self.specialist_model.predict(clean_text, k=1)
        lbl2 = p2[0].replace("__label__", "").strip().lower()
        return lbl2

    def predict_batch(self, texts: List[str]) -> List[str]:
        return [self.predict(t) for t in texts]


# ------------------------------------------------------------------------------
# 1. FastText LID-176 Two-Stage Router
# ------------------------------------------------------------------------------
class FastTextTwoStageRouter(BaseTwoStageRouter):
    def __init__(self, stock_path: Optional[str] = None, specialist_path: Optional[str] = None):
        self.stock_path = stock_path or os.path.join(PROJ_ROOT, "models", "lid.176.bin")
        if not os.path.exists(self.stock_path):
            alt = os.path.join(PROJ_ROOT, "models", "benchmark", "fastText", "lid.176.bin")
            if os.path.exists(alt):
                self.stock_path = alt
        if not os.path.exists(self.stock_path):
            raise FileNotFoundError(f"FastText stock model not found at {self.stock_path}")
        
        self.stock_model = fasttext.load_model(fix_win_path(self.stock_path))
        super().__init__(name="FastText-LID-176-TwoStage", specialist_path=specialist_path)

    def predict_stage1(self, text: str) -> str:
        p, _ = self.stock_model.predict(text, k=1)
        return p[0].replace("__label__", "")

    def is_sinhala_script(self, raw_stage1_label: str) -> bool:
        return raw_stage1_label == "si"

    def map_global_label(self, raw_stage1_label: str) -> str:
        return BCP47_TO_COMMON.get(raw_stage1_label, raw_stage1_label)


# ------------------------------------------------------------------------------
# 2. OpenLID-v2 Two-Stage Router
# ------------------------------------------------------------------------------
class OpenLIDTwoStageRouter(BaseTwoStageRouter):
    def __init__(self, stock_path: Optional[str] = None, specialist_path: Optional[str] = None):
        self.stock_path = stock_path or os.path.join(PROJ_ROOT, "models", "benchmark", "OpenLID", "model.bin")
        if not os.path.exists(self.stock_path):
            self.stock_path = hf_hub_download(repo_id="laurievb/OpenLID-v2", filename="model.bin")
        
        self.stock_model = fasttext.load_model(fix_win_path(self.stock_path))
        
        # OpenLID fine-tuned specialist default
        openlid_specialist = specialist_path or os.path.join(PROJ_ROOT, "models", "openlid_v2_finetuned.bin")
        if not os.path.exists(openlid_specialist):
            openlid_specialist = os.path.join(PROJ_ROOT, "data_pipeline", "models", "openlid_v2_finetuned.bin")
        if not os.path.exists(openlid_specialist):
            openlid_specialist = None  # fallback to fasttext specialist
            
        super().__init__(name="OpenLID-v2-TwoStage", specialist_path=openlid_specialist)

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


# ------------------------------------------------------------------------------
# 3. NLLB LID-218 Two-Stage Router
# ------------------------------------------------------------------------------
class NLLBLIDTwoStageRouter(BaseTwoStageRouter):
    def __init__(self, stock_path: Optional[str] = None, specialist_path: Optional[str] = None):
        self.stock_path = stock_path or os.path.join(PROJ_ROOT, "models", "benchmark", "NLLB", "model.bin")
        if not os.path.exists(self.stock_path):
            self.stock_path = hf_hub_download(repo_id="facebook/fasttext-language-identification", filename="model.bin")
        
        self.stock_model = fasttext.load_model(fix_win_path(self.stock_path))
        super().__init__(name="NLLB-LID-218-TwoStage", specialist_path=specialist_path)

    def predict_stage1(self, text: str) -> str:
        p, _ = self.stock_model.predict(text, k=1)
        return p[0].replace("__label__", "")

    def is_sinhala_script(self, raw_stage1_label: str) -> bool:
        return raw_stage1_label == "sin_Sinh"

    def map_global_label(self, raw_stage1_label: str) -> str:
        return BCP47_TO_COMMON.get(raw_stage1_label, raw_stage1_label)


# ------------------------------------------------------------------------------
# 4. GlotLID v3 Two-Stage Router
# ------------------------------------------------------------------------------
class GlotLIDTwoStageRouter(BaseTwoStageRouter):
    def __init__(self, stock_path: Optional[str] = None, specialist_path: Optional[str] = None):
        self.stock_path = stock_path or os.path.join(PROJ_ROOT, "models", "benchmark", "GlotLID", "model.bin")
        if not os.path.exists(self.stock_path):
            self.stock_path = hf_hub_download(repo_id="cis-lmu/glotlid", filename="model.bin")
        
        self.stock_model = fasttext.load_model(fix_win_path(self.stock_path))
        super().__init__(name="GlotLID-v3-TwoStage", specialist_path=specialist_path)

    def predict_stage1(self, text: str) -> str:
        p, _ = self.stock_model.predict(text, k=1)
        return p[0].replace("__label__", "")

    def is_sinhala_script(self, raw_stage1_label: str) -> bool:
        return raw_stage1_label == "sin_Sinh"

    def map_global_label(self, raw_stage1_label: str) -> str:
        return BCP47_TO_COMMON.get(raw_stage1_label, raw_stage1_label)


# ------------------------------------------------------------------------------
# 5. ConLID Two-Stage Router
# ------------------------------------------------------------------------------
class ConLIDTwoStageRouter(BaseTwoStageRouter):
    def __init__(self, repo_dir: Optional[str] = None, checkpoints_dir: Optional[str] = None, specialist_path: Optional[str] = None):
        self.repo_dir = repo_dir or os.path.join(PROJ_ROOT, "models", "benchmark", "ConLID", "repo")
        self.checkpoints_dir = checkpoints_dir or os.path.join(PROJ_ROOT, "models", "benchmark", "ConLID", "checkpoints")
        
        if not os.path.exists(os.path.join(self.repo_dir, "model.py")):
            raise FileNotFoundError(f"ConLID repository wrapper not found at {self.repo_dir}. Run scripts/download_and_verify_models.py first.")
        
        if not os.path.exists(self.checkpoints_dir):
            raise FileNotFoundError(f"ConLID checkpoints not found at {self.checkpoints_dir}. Run scripts/download_and_verify_models.py first.")

        # Dynamically import ConLID
        if self.repo_dir not in sys.path:
            sys.path.insert(0, self.repo_dir)
        
        from model import ConLID
        print("Loading ConLID stock model...")
        self.conlid_model = ConLID.from_pretrained(dir=self.checkpoints_dir)
        super().__init__(name="ConLID-TwoStage", specialist_path=specialist_path)

    def predict_stage1(self, text: str) -> str:
        pred_result = self.conlid_model.predict(text, k=1)
        return pred_result[0][0]

    def is_sinhala_script(self, raw_stage1_label: str) -> bool:
        return raw_stage1_label == "sin_Sinh"

    def map_global_label(self, raw_stage1_label: str) -> str:
        return BCP47_TO_COMMON.get(raw_stage1_label, raw_stage1_label)


# ------------------------------------------------------------------------------
# Factory Function
# ------------------------------------------------------------------------------
def get_two_stage_router(model_name: str, specialist_path: Optional[str] = None) -> BaseTwoStageRouter:
    name = model_name.lower().replace("-", "").replace("_", "")
    if "fasttext" in name:
        return FastTextTwoStageRouter(specialist_path=specialist_path)
    elif "openlid" in name:
        return OpenLIDTwoStageRouter(specialist_path=specialist_path)
    elif "nllb" in name:
        return NLLBLIDTwoStageRouter(specialist_path=specialist_path)
    elif "glotlid" in name:
        return GlotLIDTwoStageRouter(specialist_path=specialist_path)
    elif "conlid" in name:
        return ConLIDTwoStageRouter(specialist_path=specialist_path)
    else:
        raise ValueError(f"Unknown model name: {model_name}. Choose from: fasttext, openlid, nllb, glotlid, conlid.")
