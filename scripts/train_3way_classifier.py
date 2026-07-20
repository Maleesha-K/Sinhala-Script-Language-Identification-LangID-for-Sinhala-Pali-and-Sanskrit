import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

INPUT_CSV = r"data\processed\3way_master.csv"
VIS_DIR = r"data\processed\visualizations_3way"

def main():
    if not os.path.exists(VIS_DIR):
        os.makedirs(VIS_DIR)

    print(f"1. Loading prepared master dataset: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV, encoding='utf-8-sig')
    
    # 2. Extract splits
    print("2. Extracting Train/Val/Test splits...")
    train_df = df[df['split'] == 'train']
    val_df = df[df['split'] == 'val']
    test_df = df[df['split'] == 'test']
    
    print(f"Train rows: {len(train_df)}")
    print(f"Val rows:   {len(val_df)}")
    print(f"Test rows:  {len(test_df)}")
    
    # 3. Vectorization and Training
    print("\n3. Training 3-Way Baseline Model (TF-IDF + Logistic Regression)...")
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 4), max_features=10000)
    
    X_train = vectorizer.fit_transform(train_df['text'].astype(str))
    y_train = train_df['label']
    
    X_val = vectorizer.transform(val_df['text'].astype(str))
    y_val = val_df['label']
    
    X_test = vectorizer.transform(test_df['text'].astype(str))
    y_test = test_df['label']
    
    model = LogisticRegression(max_iter=1000, class_weight='balanced', multi_class='multinomial')
    model.fit(X_train, y_train)
    
    # 4. Validation
    train_preds = model.predict(X_train)
    val_preds = model.predict(X_val)
    train_acc = accuracy_score(y_train, train_preds)
    val_acc = accuracy_score(y_val, val_preds)
    
    print("\n--- Validation Check ---")
    print(f"Training Accuracy:   {train_acc:.4f}")
    print(f"Validation Accuracy: {val_acc:.4f}")
    
    if train_acc - val_acc > 0.05:
        print("Warning: Model might be OVERFITTING.")
    elif train_acc < 0.70 and val_acc < 0.70:
        print("Warning: Model might be UNDERFITTING.")
    else:
        print("Model fit looks excellent (no massive overfitting).")
    
    # 5. Test Evaluation
    print("\n--- Test Set Evaluation ---")
    test_preds = model.predict(X_test)
    print(classification_report(y_test, test_preds))
    
    # 6. Visualizations
    print("\n5. Generating Visualizations...")
    labels = model.classes_
    cm = confusion_matrix(y_test, test_preds, labels=labels)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
    plt.title('Confusion Matrix: Sinhala vs Pali vs Sanskrit')
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.savefig(os.path.join(VIS_DIR, 'confusion_matrix.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    svd = TruncatedSVD(n_components=2, random_state=42)
    X_test_2d = svd.fit_transform(X_test)
    
    plt.figure(figsize=(10, 8))
    colors = {'pali': 'green', 'sinhala': 'orange', 'sanskrit': 'blue'}
    for label in np.unique(y_test):
        idx = (y_test == label)
        plt.scatter(X_test_2d[idx, 0], X_test_2d[idx, 1], 
                    c=colors.get(label, 'red'), label=label.capitalize(), alpha=0.6, edgecolors='w', s=50)
        
    plt.title('2D PCA of TF-IDF Embeddings (Test Split)')
    plt.xlabel('Component 1')
    plt.ylabel('Component 2')
    plt.legend(title='Language')
    plt.savefig(os.path.join(VIS_DIR, 'scatter_plot_2d.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Visualizations successfully saved to {VIS_DIR}")

if __name__ == "__main__":
    main()
