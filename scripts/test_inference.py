import joblib
import sys
import os

# Fix Windows console Unicode print errors
sys.stdout.reconfigure(encoding='utf-8')

MODEL_DIR = r"models"
VEC_PATH = os.path.join(MODEL_DIR, "langid_vectorizer.pkl")
MODEL_PATH = os.path.join(MODEL_DIR, "langid_model.pkl")

def load_model():
    if not os.path.exists(VEC_PATH) or not os.path.exists(MODEL_PATH):
        print("Model or vectorizer not found. Run export_3way_model.py first.")
        sys.exit(1)
        
    vectorizer = joblib.load(VEC_PATH)
    model = joblib.load(MODEL_PATH)
    return vectorizer, model

def predict_language(text, vectorizer, model):
    if not text or not text.strip():
        return "Unknown"
        
    # The SRS requires treating the whole string as a single input
    X = vectorizer.transform([text.strip()])
    
    # Get prediction and probabilities
    pred = model.predict(X)[0]
    probs = model.predict_proba(X)[0]
    
    classes = model.classes_
    prob_dict = {classes[i]: probs[i] for i in range(len(classes))}
    
    return pred, prob_dict

import argparse

def main():
    parser = argparse.ArgumentParser(description="Test LangID Inference")
    parser.add_argument("--text", type=str, help="Text to classify")
    args = parser.parse_args()

    print("Loading models...")
    vectorizer, model = load_model()
    print("Models loaded successfully.\n")
    
    if args.text:
        pred, probs = predict_language(args.text, vectorizer, model)
        print(f"Text: {args.text}")
        print(f"Predicted Language: {pred.upper()}")
        print(f"Probabilities: {probs}")
    else:
        print("Please provide text using the --text argument.")

if __name__ == "__main__":
    main()
