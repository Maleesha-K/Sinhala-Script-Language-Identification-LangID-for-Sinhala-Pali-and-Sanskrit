from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import os

app = FastAPI(
    title="Sinhala-Script LangID API",
    description="API for classifying text into Sinhala, Pali, or Sanskrit.",
    version="1.0.0"
)

# Define request/response schemas
class PredictRequest(BaseModel):
    text: str

class PredictResponse(BaseModel):
    text: str
    language: str
    confidence: float
    probabilities: dict

# Load models on startup
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
VEC_PATH = os.path.join(MODEL_DIR, "langid_vectorizer.pkl")
MODEL_PATH = os.path.join(MODEL_DIR, "langid_model.pkl")

try:
    vectorizer = joblib.load(VEC_PATH)
    model = joblib.load(MODEL_PATH)
except Exception as e:
    vectorizer = None
    model = None
    print(f"Error loading models: {e}. Please ensure models are exported to {MODEL_DIR}")

@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    if not vectorizer or not model:
        raise HTTPException(status_code=503, detail="Models are not loaded.")

    text = request.text.strip()
    
    # Gracefully handle empty or unsupported inputs
    if not text:
        return PredictResponse(
            text=text,
            language="Unknown",
            confidence=0.0,
            probabilities={}
        )

    # Dynamic Processing: process the entire string as a single input
    try:
        X = vectorizer.transform([text])
        pred = model.predict(X)[0]
        probs = model.predict_proba(X)[0]
        
        classes = model.classes_
        prob_dict = {classes[i]: round(float(probs[i]), 4) for i in range(len(classes))}
        confidence = prob_dict[pred]
        
        return PredictResponse(
            text=text,
            language=pred.upper(),
            confidence=confidence,
            probabilities=prob_dict
        )
    except Exception as e:
        # Fallback for unexpected failures (e.g., extremely long strings that break memory, though unlikely here)
        return PredictResponse(
            text=text,
            language="Unknown",
            confidence=0.0,
            probabilities={}
        )

@app.get("/health")
async def health_check():
    if vectorizer and model:
        return {"status": "ok", "models_loaded": True}
    return {"status": "error", "models_loaded": False}
