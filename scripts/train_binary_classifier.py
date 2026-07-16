import pandas as pd
import numpy as np
import os
from sklearn.model_selection import GroupShuffleSplit
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

PALI_CSV = r"data\processed\pali_only_dataset.csv"
SINHALA_CSV = r"data\processed\Sinhala_sidiac_common.csv"
OUTPUT_CSV = r"data\processed\binary_master.csv"

def split_grouped_data(df, train_size=0.8, val_size=0.1, test_size=0.1, random_state=42):
    """Splits a dataframe into train/val/test using GroupShuffleSplit to prevent data leakage."""
    # First split into train and temp (val + test)
    gss1 = GroupShuffleSplit(n_splits=1, train_size=train_size, random_state=random_state)
    train_idx, temp_idx = next(gss1.split(df, groups=df['group_id']))
    
    train_df = df.iloc[train_idx].copy()
    temp_df = df.iloc[temp_idx].copy()
    
    # Now split temp into val and test
    # The proportion of val relative to temp is val_size / (val_size + test_size)
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
    print("1. Loading datasets with utf-8-sig to handle encoding gracefully...")
    # Using utf-8-sig handles potential Byte Order Marks (BOM) that cause garbled output
    try:
        df_pali = pd.read_csv(PALI_CSV, encoding='utf-8-sig')
        df_sinhala = pd.read_csv(SINHALA_CSV, encoding='utf-8-sig')
    except Exception as e:
        print(f"Error reading CSVs: {e}")
        return

    print(f"Initial counts - Pali: {len(df_pali)}, Sinhala: {len(df_sinhala)}")
    
    # 2. Balance the dataset (Stratified)
    print("\n2. Balancing datasets by downsampling the majority class...")
    min_count = min(len(df_pali), len(df_sinhala))
    
    # Downsample by sampling randomly but maintaining groups where possible isn't strictly necessary for balancing total rows,
    # but simple random sampling of rows is fine here.
    df_pali_balanced = df_pali.sample(n=min_count, random_state=42).copy()
    df_sinhala_balanced = df_sinhala.sample(n=min_count, random_state=42).copy()
    
    print(f"Balanced counts - Pali: {len(df_pali_balanced)}, Sinhala: {len(df_sinhala_balanced)}")

    # 3. Stratified Group Splitting (Zero-Leakage)
    print("\n3. Performing Zero-Leakage Grouped Split for each language independently...")
    train_p, val_p, test_p = split_grouped_data(df_pali_balanced)
    train_s, val_s, test_s = split_grouped_data(df_sinhala_balanced)
    
    # Combine the splits to form a balanced training/val/test set
    train_df = pd.concat([train_p, train_s])
    val_df = pd.concat([val_p, val_s])
    test_df = pd.concat([test_p, test_s])
    
    final_df = pd.concat([train_df, val_df, test_df]).sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Verification: Zero Data Leakage check
    train_groups = set(train_df['group_id'])
    val_groups = set(val_df['group_id'])
    test_groups = set(test_df['group_id'])
    
    assert len(train_groups.intersection(val_groups)) == 0, "Leakage between Train and Val!"
    assert len(train_groups.intersection(test_groups)) == 0, "Leakage between Train and Test!"
    assert len(val_groups.intersection(test_groups)) == 0, "Leakage between Val and Test!"
    print("Zero-Leakage verification PASSED. No overlapping group_ids across splits.")
    
    # Save master dataset
    final_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"Saved merged dataset to {OUTPUT_CSV}")
    
    # 4. Train Model
    print("\n4. Training Baseline Model (TF-IDF + Logistic Regression)...")
    # Using char n-grams is highly effective for LangID
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 4), max_features=10000)
    
    X_train = vectorizer.fit_transform(train_df['text'].astype(str))
    y_train = train_df['label']
    
    X_val = vectorizer.transform(val_df['text'].astype(str))
    y_val = val_df['label']
    
    X_test = vectorizer.transform(test_df['text'].astype(str))
    y_test = test_df['label']
    
    model = LogisticRegression(max_iter=1000, class_weight='balanced')
    model.fit(X_train, y_train)
    
    # 5. Evaluate Validation (Overfit/Underfit check)
    train_preds = model.predict(X_train)
    val_preds = model.predict(X_val)
    
    train_acc = accuracy_score(y_train, train_preds)
    val_acc = accuracy_score(y_val, val_preds)
    
    print("\n--- Validation Check (Overfitting/Underfitting Analysis) ---")
    print(f"Training Accuracy:   {train_acc:.4f}")
    print(f"Validation Accuracy: {val_acc:.4f}")
    
    if train_acc - val_acc > 0.05:
        print("Warning: Model might be OVERFITTING (Training accuracy is significantly higher than Validation).")
    elif train_acc < 0.70 and val_acc < 0.70:
        print("Warning: Model might be UNDERFITTING (Both Training and Validation accuracies are low).")
    else:
        print("Model fit looks healthy (Train and Val metrics are close and reasonably high).")
        
    # 6. Evaluate Test
    print("\n--- Test Set Evaluation ---")
    test_preds = model.predict(X_test)
    print("Classification Report:")
    print(classification_report(y_test, test_preds))
    
    print("Confusion Matrix:")
    labels = model.classes_
    cm = confusion_matrix(y_test, test_preds, labels=labels)
    cm_df = pd.DataFrame(cm, index=[f"True_{l}" for l in labels], columns=[f"Pred_{l}" for l in labels])
    print(cm_df)

if __name__ == "__main__":
    main()
