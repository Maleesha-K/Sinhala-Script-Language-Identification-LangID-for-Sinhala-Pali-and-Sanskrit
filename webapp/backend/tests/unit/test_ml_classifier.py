import pytest
from unittest.mock import MagicMock, patch
import numpy as np
from app.ml.sklearn_langid import SklearnLangIDClassifier

def test_classifier_predict_empty_and_whitespace():
    """Verify classifier returns 'unknown' for empty or whitespace-only inputs without invoking model."""
    with patch.object(SklearnLangIDClassifier, '_load_models'):
        classifier = SklearnLangIDClassifier()
        classifier.model = MagicMock()
        classifier.vectorizer = MagicMock()
        
        assert classifier.predict("") == "unknown"
        assert classifier.predict("   \n\t  ") == "unknown"
        assert classifier.predict(None) == "unknown"
        
        classifier.model.predict.assert_not_called()

def test_classifier_predict_single_text_success():
    """Verify single text prediction returns the predicted class string."""
    with patch.object(SklearnLangIDClassifier, '_load_models'):
        classifier = SklearnLangIDClassifier()
        
        mock_vec = MagicMock()
        mock_model = MagicMock()
        mock_model.predict.return_value = ["sinhala"]
        
        classifier.vectorizer = mock_vec
        classifier.model = mock_model
        
        result = classifier.predict("මෙය සිංහල වාක්‍යයකි.")
        assert result == "sinhala"
        mock_vec.transform.assert_called_once_with(["මෙය සිංහල වාක්‍යයකි."])
        mock_model.predict.assert_called_once()

def test_classifier_predict_batch_with_probabilities():
    """Verify batch prediction calculates probabilities dictionary and maximum confidence score."""
    with patch.object(SklearnLangIDClassifier, '_load_models'):
        classifier = SklearnLangIDClassifier()
        
        mock_vec = MagicMock()
        mock_model = MagicMock()
        mock_model.classes_ = np.array(["pali", "sanskrit", "sinhala"])
        mock_model.predict.return_value = np.array(["sinhala", "pali"])
        mock_model.predict_proba.return_value = np.array([
            [0.02, 0.03, 0.95],
            [0.91, 0.05, 0.04]
        ])
        
        classifier.vectorizer = mock_vec
        classifier.model = mock_model
        
        texts = ["සිංහල පාඨය", "නමෝ තස්ස"]
        results = classifier.predict_batch(texts)
        
        assert len(results) == 2
        # First sample
        assert results[0]["language"] == "sinhala"
        assert pytest.approx(results[0]["confidence"], 0.01) == 0.95
        assert results[0]["probabilities"]["sinhala"] == 0.95
        assert results[0]["probabilities"]["pali"] == 0.02
        assert results[0]["probabilities"]["sanskrit"] == 0.03
        
        # Second sample
        assert results[1]["language"] == "pali"
        assert pytest.approx(results[1]["confidence"], 0.01) == 0.91
        assert results[1]["probabilities"]["pali"] == 0.91

def test_classifier_predict_batch_empty_list():
    """Verify batch prediction returns empty list for empty input."""
    with patch.object(SklearnLangIDClassifier, '_load_models'):
        classifier = SklearnLangIDClassifier()
        classifier.model = MagicMock()
        classifier.vectorizer = MagicMock()
        
        assert classifier.predict_batch([]) == []

def test_classifier_missing_model_raises_runtime_error():
    """Verify calling predict when model/vectorizer is None raises RuntimeError."""
    with patch.object(SklearnLangIDClassifier, '_load_models'):
        classifier = SklearnLangIDClassifier()
        classifier.model = None
        classifier.vectorizer = None
        
        with pytest.raises(RuntimeError, match="Model or vectorizer is not loaded"):
            classifier.predict("පෙළ")
            
        with pytest.raises(RuntimeError, match="Model or vectorizer is not loaded"):
            classifier.predict_batch(["පෙළ"])

def test_classifier_load_models_file_not_found():
    """Verify _load_models raises FileNotFoundError if model path does not exist."""
    with pytest.raises(FileNotFoundError):
        SklearnLangIDClassifier(model_path="nonexistent_model.pkl", vectorizer_path="nonexistent_vec.pkl")
