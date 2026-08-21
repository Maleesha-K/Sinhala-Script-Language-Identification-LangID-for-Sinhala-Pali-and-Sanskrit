import os
import joblib
import logging
from typing import List, Dict
from app.ml.base import BaseClassifier

logger = logging.getLogger(__name__)

class SklearnLangIDClassifier(BaseClassifier):
    """
    Implementation of the Language Identification model using the pre-trained 
    scikit-learn models (langid_model.pkl and langid_vectorizer.pkl).
    """
    
    def __init__(self, model_path: str = None, vectorizer_path: str = None):
        # Default paths assuming we run from webapp/backend and models are in the root directory
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
        self.model_path = model_path or os.path.join(root_dir, "models", "langid_model.pkl")
        self.vectorizer_path = vectorizer_path or os.path.join(root_dir, "models", "langid_vectorizer.pkl")
        
        self.model = None
        self.vectorizer = None
        self._load_models()
        
    def _load_models(self):
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model file not found at {self.model_path}")
            if not os.path.exists(self.vectorizer_path):
                raise FileNotFoundError(f"Vectorizer file not found at {self.vectorizer_path}")
                
            self.model = joblib.load(self.model_path)
            self.vectorizer = joblib.load(self.vectorizer_path)
            logger.info("Successfully loaded sklearn LangID model and vectorizer.")
        except Exception as e:
            logger.error(f"Failed to load ML models: {e}")
            raise
            
    def predict(self, text: str) -> str:
        if not self.model or not self.vectorizer:
            raise RuntimeError("Model or vectorizer is not loaded.")
            
        if not text or not text.strip():
            return "unknown"
            
        X = self.vectorizer.transform([text])
        prediction = self.model.predict(X)
        return prediction[0]
        
    def predict_batch(self, texts: List[str]) -> List[Dict]:
        if not self.model or not self.vectorizer:
            raise RuntimeError("Model or vectorizer is not loaded.")
            
        if not texts:
            return []
            
        X = self.vectorizer.transform(texts)
        predictions = self.model.predict(X)
        
        results = []
        if hasattr(self.model, "predict_proba"):
            probas = self.model.predict_proba(X)
            classes = self.model.classes_
            
            for i, pred in enumerate(predictions):
                prob_dict = {str(classes[j]): float(probas[i][j]) for j in range(len(classes))}
                max_prob = float(max(probas[i]))
                results.append({
                    "language": str(pred),
                    "confidence": max_prob,
                    "probabilities": prob_dict
                })
        else:
            for pred in predictions:
                results.append({
                    "language": str(pred),
                    "confidence": 0.99,
                    "probabilities": {str(pred): 0.99}
                })
                
        return results

# Singleton instance to avoid reloading the model on every task
langid_classifier = SklearnLangIDClassifier()
