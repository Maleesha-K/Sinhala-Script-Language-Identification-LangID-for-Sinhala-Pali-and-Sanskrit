from abc import ABC, abstractmethod
from typing import List, Dict

class BaseClassifier(ABC):
    """
    Abstract base class for Language Identification ML models.
    """
    
    @abstractmethod
    def predict(self, text: str) -> str:
        """
        Predicts the language of a given text.
        
        Args:
            text (str): The text to classify.
            
        Returns:
            str: The predicted language (e.g., 'sinhala', 'pali', 'sanskrit').
        """
        pass
        
    @abstractmethod
    def predict_batch(self, texts: List[str]) -> List[str]:
        """
        Predicts the languages for a batch of texts.
        
        Args:
            texts (List[str]): A list of texts to classify.
            
        Returns:
            List[str]: A list of predicted languages corresponding to the input texts.
        """
        pass
