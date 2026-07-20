import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import GroupShuffleSplit
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

SINHALA_CSV = r"data\processed\Sinhala_sidiac_common.csv"
SANSKRIT_CSV = r"data\processed\sanskrit_sansin_common.csv"
OUTPUT_CSV = r"data\processed\sinhala_sanskrit_master.csv"
VIS_DIR = r"data\processed\visualizations_sin_san"

def split_grouped_data(df, train_size=0.8, val_size=0.1, test_size=0.1, random_state=42):
    """Splits a dataframe into train/val/test using GroupShuffleSplit to prevent data leakage."""
    gss1 = GroupShuffleSplit(n_splits=1, train_size=train_size, random_state=random_state)
    train_idx, temp_idx = next(gss1.split(df, groups=df['group_id']))
    
    train_df = df.iloc[train_idx].copy()
    temp_df = df.iloc[temp_idx].copy()
    
    val_proportion = val_size / (val_size + test_size)
    gss2 = GroupShuffleSplit(n_splits=1, train_size=val_proportion, random_state=random_state)
    val_idx, test_idx = next(gss2.split(temp_df, groups=temp_df['group_id']))
    
    val_df = temp_df.iloc[val_idx].copy()
    test_df = temp_df.iloc[test_idx].copy()
    
    train_df['split'] = 'train'
    val_df['split'] = 'val'
    test_df['split'] = 'test'
    
    return train_df, val_df, test_df

def main():
    if not os.path.exists(VIS_DIR):
        os.makedirs(VIS_DIR)

    print("1. Loading datasets with utf-8-sig...")
    df_sinhala = pd.read_csv(SINHALA_CSV, encoding='utf-8-sig')
    df_sanskrit = pd.read_csv(SANSKRIT_CSV, encoding='utf-8-sig')
    
    print(f"Initial counts - Sinhala: {len(df_sinhala)}, Sanskrit: {len(df_sanskrit)}")
    
    print("\n2. Balancing datasets by downsampling the majority class...")
    min_count = min(len(df_sinhala), len(df_sanskrit))
    
    df_sinhala_balanced = df_sinhala.sample(n=min_count, random_state=42).copy()
    df_sanskrit_balanced = df_sanskrit.sample(n=min_count, random_state=42).copy()
    
    print(f"Balanced counts - Sinhala: {len(df_sinhala_balanced)}, Sanskrit: {len(df_sanskrit_balanced)}")

    print("\n3. Performing Zero-Leakage Grouped Split...")
    train_s, val_s, test_s = split_grouped_data(df_sinhala_balanced)
    train_sa, val_sa, test_sa = split_grouped_data(df_sanskrit_balanced)
    
    train_df = pd.concat([train_s, train_sa])
    val_df = pd.concat([val_s, val_sa])
    test_df = pd.concat([test_s, test_sa])
    
    final_df = pd.concat([train_df, val_df, test_df]).sample(frac=1, random_state=42).reset_index(drop=True)
    
    train_groups = set(train_df['group_id'])
    val_groups = set(val_df['group_id'])
    test_groups = set(test_df['group_id'])
    
    assert len(train_groups.intersection(val_groups)) == 0, "Leakage between Train and Val!"
    assert len(train_groups.intersection(test_groups)) == 0, "Leakage between Train and Test!"
    assert len(val_groups.intersection(test_groups)) == 0, "Leakage between Val and Test!"
    print("Zero-Leakage verification PASSED.")
    
    final_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"Saved merged dataset to {OUTPUT_CSV}")
    
    print("\n4. Training Baseline Model (TF-IDF + Logistic Regression)...")
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 4), max_features=10000)
    
    X_train = vectorizer.fit_transform(train_df['text'].astype(str))
    y_train = train_df['label']
    X_val = vectorizer.transform(val_df['text'].astype(str))
    y_val = val_df['label']
    X_test = vectorizer.transform(test_df['text'].astype(str))
    y_test = test_df['label']
    
    model = LogisticRegression(max_iter=1000, class_weight='balanced')
    model.fit(X_train, y_train)
    
    train_preds = model.predict(X_train)
    val_preds = model.predict(X_val)
    train_acc = accuracy_score(y_train, train_preds)
    val_acc = accuracy_score(y_val, val_preds)
    
    print("\n--- Validation Check ---")
    print(f"Training Accuracy:   {train_acc:.4f}")
    print(f"Validation Accuracy: {val_acc:.4f}")
    
    print("\n--- Test Set Evaluation ---")
    test_preds = model.predict(X_test)
    print(classification_report(y_test, test_preds))
    
    # 5. Visualizations
    print("\n5. Generating Visualizations...")
    labels = model.classes_
    cm = confusion_matrix(y_test, test_preds, labels=labels)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
    plt.title('Confusion Matrix: Sinhala vs Sanskrit')
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.savefig(os.path.join(VIS_DIR, 'confusion_matrix.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    svd = TruncatedSVD(n_components=2, random_state=42)
    X_test_2d = svd.fit_transform(X_test)
    
    plt.figure(figsize=(10, 8))
    colors = {labels[0]: 'blue', labels[1]: 'orange'}
    for label in np.unique(y_test):
        idx = (y_test == label)
        plt.scatter(X_test_2d[idx, 0], X_test_2d[idx, 1], 
                    c=colors.get(label, 'red'), label=label, alpha=0.6, edgecolors='w', s=50)
        
    plt.title('2D Visualization of Text Embeddings (Sinhala vs Sanskrit)')
    plt.xlabel('Component 1')
    plt.ylabel('Component 2')
    plt.legend(title='Language')
    plt.savefig(os.path.join(VIS_DIR, 'scatter_plot_2d.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Visualizations saved to {VIS_DIR}")

if __name__ == "__main__":
    main()
