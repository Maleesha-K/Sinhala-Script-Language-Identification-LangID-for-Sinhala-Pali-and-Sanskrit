import os
import sys
from huggingface_hub import HfApi, create_repo

def upload_to_huggingface():
    # 1. Check for Hugging Face token in environment
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        print("Error: HF_TOKEN environment variable not set.")
        print("Please set your Hugging Face token before running this script.")
        print("Example (Windows PowerShell): $env:HF_TOKEN='your_hf_token'")
        sys.exit(1)

    print("Authenticating with Hugging Face Hub...")
    api = HfApi(token=hf_token)
    username = api.whoami()["name"]
    print(f"Logged in as: {username}")

    # Define paths
    proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    datasets_dir = os.path.join(proj_root, "datasets", "preprocessed")
    models_dir = os.path.join(proj_root, "models")

    # 2. Upload Benchmark Datasets
    dataset_repo_id = f"{username}/Sinhala-Script-LangID-Benchmark"
    print(f"\n--- Uploading Datasets to {dataset_repo_id} ---")
    
    try:
        create_repo(repo_id=dataset_repo_id, repo_type="dataset", exist_ok=True, private=False)
        print(f"Dataset repository '{dataset_repo_id}' is ready.")
        
        # Upload all JSONL files in the preprocessed directory
        if os.path.exists(datasets_dir):
            for filename in os.listdir(datasets_dir):
                if filename.endswith(".jsonl"):
                    file_path = os.path.join(datasets_dir, filename)
                    print(f"Uploading {filename}...")
                    api.upload_file(
                        path_or_fileobj=file_path,
                        path_in_repo=f"data/{filename}",
                        repo_id=dataset_repo_id,
                        repo_type="dataset"
                    )
            print("Preprocessed JSONL dataset upload complete!")
        else:
            print(f"Warning: Dataset directory {datasets_dir} not found. Skipping dataset upload.")
            
        # Upload Nadil's custom CSV datasets
        nadil_data_dir = os.path.join(proj_root, "data", "Nadil")
        if os.path.exists(nadil_data_dir):
            for filename in ["train.csv", "val.csv", "test.csv"]:
                file_path = os.path.join(nadil_data_dir, filename)
                if os.path.exists(file_path):
                    print(f"Uploading custom dataset {filename}...")
                    api.upload_file(
                        path_or_fileobj=file_path,
                        path_in_repo=f"data/Nadil/{filename}",
                        repo_id=dataset_repo_id,
                        repo_type="dataset"
                    )
            print("Custom CSV dataset upload complete!")
        else:
            print(f"Warning: Custom dataset directory {nadil_data_dir} not found.")

    except Exception as e:
        print(f"Failed to upload datasets: {e}")

    # 3. Upload Fine-Tuned Models
    model_repo_id = f"{username}/FastText-Sinhala-Script-LID"
    print(f"\n--- Uploading Models to {model_repo_id} ---")
    
    try:
        create_repo(repo_id=model_repo_id, repo_type="model", exist_ok=True, private=False)
        print(f"Model repository '{model_repo_id}' is ready.")
        
        models_to_upload = [
            "fasttext_finetuned.bin",
            "langid_model.pkl",
            "langid_vectorizer.pkl"
        ]
        
        if os.path.exists(models_dir):
            for filename in models_to_upload:
                file_path = os.path.join(models_dir, filename)
                if os.path.exists(file_path):
                    print(f"Uploading {filename}...")
                    api.upload_file(
                        path_or_fileobj=file_path,
                        path_in_repo=filename,
                        repo_id=model_repo_id,
                        repo_type="model"
                    )
                else:
                    print(f"Note: {filename} not found locally, skipping.")
            print("Model upload complete!")
        else:
            print(f"Warning: Models directory {models_dir} not found. Skipping model upload.")
            
    except Exception as e:
        print(f"Failed to upload models: {e}")

    print("\n=======================================================")
    print("All tasks completed! Check your Hugging Face profile at:")
    print(f"https://huggingface.co/{username}")
    print("=======================================================")

if __name__ == "__main__":
    upload_to_huggingface()
