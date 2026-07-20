import pandas as pd
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

INPUT_CSV = r"data\processed\3way_master.csv"
MODEL_DIR = r"models"

def main():
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)

    print(f"Loading prepared master dataset: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV, encoding='utf-8-sig')
    
    # We will train on the 'train' split to be consistent with our evaluation
    train_df = df[df['split'] == 'train']
    print(f"Training on {len(train_df)} rows...")
    
    print("Fitting TF-IDF Vectorizer...")
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 4), max_features=10000)
    X_train = vectorizer.fit_transform(train_df['text'].astype(str))
    y_train = train_df['label']
    
    print("Training Logistic Regression Model...")
    model = LogisticRegression(max_iter=1000, class_weight='balanced', multi_class='multinomial')
    model.fit(X_train, y_train)
    
    vec_path = os.path.join(MODEL_DIR, "langid_vectorizer.pkl")
    model_path = os.path.join(MODEL_DIR, "langid_model.pkl")
    
    print("Exporting models via joblib...")
    joblib.dump(vectorizer, vec_path)
    joblib.dump(model, model_path)
    
    print(f"Successfully exported vectorizer to: {vec_path}")
    print(f"Successfully exported model to: {model_path}")

if __name__ == "__main__":
    main()
