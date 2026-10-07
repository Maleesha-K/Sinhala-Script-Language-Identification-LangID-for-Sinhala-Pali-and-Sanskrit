"""
Inference Script for Character n-gram + Logistic Regression Baseline
"""
import os
import sys
import joblib

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def to_win_long(p):
    p_abs = os.path.abspath(p)
    return '\\\\?\\' + p_abs if os.name == 'nt' and not p_abs.startswith('\\\\?\\') else p_abs

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = to_win_long(os.path.join(CURRENT_DIR, "langid_model.pkl"))
VEC_PATH = to_win_long(os.path.join(CURRENT_DIR, "langid_vectorizer.pkl"))

def load_model():
    if not os.path.exists(MODEL_PATH) or not os.path.exists(VEC_PATH):
        raise FileNotFoundError("Model files not found. Train via benchmark_phase1_baselines.py first.")
    clf = joblib.load(MODEL_PATH)
    vec = joblib.load(VEC_PATH)
    return clf, vec

def predict(text, clf=None, vec=None):
    if clf is None or vec is None:
        clf, vec = load_model()
    X = vec.transform([text])
    pred = clf.predict(X)[0]
    probs = clf.predict_proba(X)[0]
    return {
        "text": text,
        "prediction": pred,
        "confidence": float(max(probs)),
        "all_probs": dict(zip(clf.classes_, map(float, probs)))
    }

if __name__ == "__main__":
    samples = [
        "ශ්‍රී ලංකාවේ අගනුවර ශ්‍රී ජයවර්ධනපුර කෝට්ටේ වේ.",
        "නමො තස්ස භගවතො අරහතො සම්මා සම්බුද්ධස්ස",
        "ධර්මක්ෂේත්‍රෙ කුරුක්ෂේත්‍රෙ සමවේතා යුයුත්සවඃ"
    ]
    clf, vec = load_model()
    print("Testing Character n-gram Logistic Regression Baseline:")
    for s in samples:
        res = predict(s, clf, vec)
        print(f"[{res['prediction'].upper()}] (conf: {res['confidence']:.4f}) -> {s[:40]}...")
