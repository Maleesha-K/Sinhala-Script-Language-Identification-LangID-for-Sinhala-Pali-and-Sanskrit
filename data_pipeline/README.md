# LangID Data Pipeline

This repository contains a modular and extensible data pipeline designed for a research project focused on Language Identification (LangID) for Sinhala, Pali, and Sanskrit written in the Sinhala script.

The pipeline handles downloading raw datasets from multiple sources (like Hugging Face), transforming them into a standardized format, running data quality checks, and eventually feeding them into benchmarking and finetuning stages.



## Architecture

The pipeline is split into distinct stages, executed sequentially via a `Makefile`. The core design principle is **Decoupled Transformation**: all upstream datasets, regardless of their original format, are transformed into a single, standardized format by a "Middle Layer" before they are processed by the downstream pipeline.

### Directory Structure

```text
data_pipeline/
├── datasets/
│   ├── raw_download/        # Untouched datasets extracted from various sources
│   └── preprocessed/        # Data transformed into the standardized pipeline format (.jsonl)
├── scripts/
│   ├── 01.download/         # Jupyter notebooks to fetch and save raw data
│   ├── 02.preprocess/       # The "Middle Layer" - transforms raw data to .jsonl
│   ├── 03.dataset_checking/ # Validation and testing scripts for the standard format
│   ├── 04.benchmark/        # Zero-shot evaluation notebooks, one per model
│   └── 05.finetune/         # Model training scripts (Placeholders)
├── Makefile                 # Orchestrates the execution of all notebooks
├── .env.example             # Template for environment variables (like HF_TOKEN)
└── README.md                # This document
```

## How It Works

The entire pipeline is orchestrated using `make` and `papermill`. Instead of using raw Python scripts, the pipeline executes parameterized Jupyter Notebooks (`.ipynb`).

### Running the Pipeline

Before running, ensure you have set up your environment variables (especially if you are downloading gated datasets from Hugging Face).

1. Copy the environment template: `cp .env.example .env`
2. Add your Hugging Face token to `.env`: `HF_TOKEN=your_token_here`

#### Local Execution (Makefile)
To run the entire pipeline locally:
```bash
make all
```

#### Google Colab Compatibility
Every notebook in this pipeline is engineered to be **100% compatible with Google Colab**.
- A standard `[COLAB SETUP]` cell is injected at the top of every notebook.
- When run in Colab, this cell automatically clones the repository, installs all necessary dependencies (via `pip`), and seamlessly mounts your Google Drive for persistent storage.
- You can simply upload any of these notebooks to Colab and run them from top to bottom without any manual environment configuration!

You can also run individual stages:

- `make download`: Runs all download notebooks.
- `make preprocess`: Runs all preprocessing notebooks.
- `make check`: Runs the dataset validation checks on all preprocessed datasets. This step now includes robust baseline checks for **Sinhala**, **Pali**, and **Sanskrit**, exporting any misclassifications to CSV files for manual review. It also supports dynamic test dataset replacement via Google Drive!
- `make benchmark`: Runs every zero-shot benchmark notebook in `04.benchmark/` (note: these download large third-party models — hundreds of MB to a few GB each — so this can take a while on a fresh machine).
- `make clean`: Deletes all downloaded and preprocessed data.

## Pipeline Standards & Conventions

To ensure the pipeline remains modular and easy to manage, please adhere to the following standards:

### 1. Naming Convention

The Makefile uses dynamic discovery based on file names. For a dataset named `my_dataset`, the following files must exist:

- `scripts/01.download/download_my_dataset.ipynb`
- `scripts/02.preprocess/preprocess_my_dataset.ipynb`

The Makefile will automatically discover these and create `make download-my_dataset` and `make preprocess-my_dataset` targets.

### 2. Standardized Format (Middle Layer)

All datasets in the `02.preprocess` stage must be transformed and saved into the `datasets/preprocessed/` directory as **JSON Lines (`.jsonl`)** files.
Every JSON object should at least contain the following schema:

```json
{
  "text": "The sample sentence...",
  "label": "sin",
  "source": "dataset_name"
}
```

*(Valid labels currently checked are `sin`, `san`, and `pli`)*

### 3. Notebook Parameterization

Notebooks are executed via `papermill`. Inputs and outputs should not be hardcoded. Instead, use a cell tagged with `parameters` at the top of your notebook.

- **Download notebooks** expect: `output_dir` (e.g., `datasets/raw_download/my_dataset`)
- **Preprocess notebooks** expect: `input_dir` and `output_file`
- **Check notebooks** expect: `input_file`
- **Benchmark notebooks** expect: `input_file` (a preprocessed `.jsonl`) and `output_file` (where per-row predictions are saved, e.g. `datasets/benchmark_results/my_model.csv`)

## How to Contribute a New Dataset

1. **Pick a Dataset Name**: Let's say your dataset is `wiki_data`.
2. **Create Download Notebook**: Create `scripts/01.download/download_wiki_data.ipynb`.
   - Add a parameter cell with `output_dir = 'datasets/raw_download/wiki_data'`.
   - Write logic to download the data and save it to `output_dir`.
3. **Create Preprocess Notebook**: Create `scripts/02.preprocess/preprocess_wiki_data.ipynb`.
   - Add a parameter cell with `input_dir = 'datasets/raw_download/wiki_data'` and `output_file = 'datasets/preprocessed/wiki_data.jsonl'`.
   - Write logic to read from `input_dir`, transform the data to match the standard JSONL schema, and write to `output_file`.
4. **Test**: Run `make all` or `make download-wiki_data && make preprocess-wiki_data` to ensure your new dataset flows through the pipeline perfectly!

## Datasets & Languages

The pipeline currently integrates the following primary datasets for robust and diverse linguistic representation:

1. **FLORES+ (Flores-200)**: A massively multilingual machine translation benchmark dataset containing high-quality translations.
2. **WiLI-2018**: The Wikipedia Language Identification dataset, providing paragraph-level text for robust baseline classification.
3. **CommonLID**: A comprehensive language identification dataset aggregated from various web sources.

### Target Benchmarking Languages
We are mainly benchmarking our models against **10 specific target languages** to evaluate performance across a diverse set of scripts and language families. The target languages are:

1. **Sinhala**
2. **Sanskrit**
3. **Pali**
4. **English**
5. **Tamil**
6. **Hindi**
7. **Bengali**
8. **Arabic**
9. **French**
10. **German**
