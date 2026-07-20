import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix
import os

INPUT_CSV = r"data\processed\binary_master.csv"
OUTPUT_DIR = r"data\processed\visualizations"

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    print("Loading data...")
    df = pd.read_csv(INPUT_CSV, encoding='utf-8-sig')
    
    # We will use the test set for the confusion matrix, and a subset for the scatter plot
    train_df = df[df['split'] == 'train']
    test_df = df[df['split'] == 'test']
    
    print("Training model for visualization...")
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 4), max_features=10000)
    X_train = vectorizer.fit_transform(train_df['text'].astype(str))
    y_train = train_df['label']
    
    X_test = vectorizer.transform(test_df['text'].astype(str))
    y_test = test_df['label']
    
    model = LogisticRegression(max_iter=1000, class_weight='balanced')
    model.fit(X_train, y_train)
    
    # --- 1. Confusion Matrix Heatmap ---
    print("Generating Confusion Matrix Heatmap...")
    test_preds = model.predict(X_test)
    labels = model.classes_
    cm = confusion_matrix(y_test, test_preds, labels=labels)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
    plt.title('Confusion Matrix: Pali vs Sinhala')
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    cm_path = os.path.join(OUTPUT_DIR, 'confusion_matrix.png')
    plt.savefig(cm_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    # --- 2. 2D Scatter Plot via TruncatedSVD (PCA for sparse matrices) ---
    print("Generating 2D Scatter Plot of Text Vectors...")
    # Reduce dimensionality to 2D
    svd = TruncatedSVD(n_components=2, random_state=42)
    # Let's plot the test set to see how well they separate
    X_test_2d = svd.fit_transform(X_test)
    
    plt.figure(figsize=(10, 8))
    # Create a scatter plot
    colors = {'pali': 'blue', 'sinhala': 'orange'}
    for label in np.unique(y_test):
        idx = (y_test == label)
        plt.scatter(X_test_2d[idx, 0], X_test_2d[idx, 1], 
                    c=colors[label], label=label, alpha=0.6, edgecolors='w', s=50)
        
    plt.title('2D Visualization of Text Embeddings (TF-IDF + SVD)')
    plt.xlabel('Component 1')
    plt.ylabel('Component 2')
    plt.legend(title='Language')
    scatter_path = os.path.join(OUTPUT_DIR, 'scatter_plot_2d.png')
    plt.savefig(scatter_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Visualizations saved to {OUTPUT_DIR}")

import numpy as np # Adding missing import for np.unique

if __name__ == "__main__":
    main()
