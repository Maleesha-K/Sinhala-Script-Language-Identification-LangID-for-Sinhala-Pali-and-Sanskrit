.PHONY: all download preprocess check benchmark finetune clean

# Environment
PYTHON := uv run python
PAPERMILL := uv run papermill

# Directories
RAW_DIR := datasets/raw_download
PREP_DIR := datasets/preprocessed
SCRIPT_DIR := scripts

# Default target runs the pipeline sequentially
all: download preprocess check benchmark finetune

# 01. Download Stage
download:
	@echo "Running download notebooks..."
	$(PAPERMILL) -k python3 -l python $(SCRIPT_DIR)/01.download/download_flores.ipynb /dev/null -p output_dir $(RAW_DIR)/flores_plus

# 02. Preprocess Stage
preprocess:
	@echo "Running preprocess notebooks..."
	$(PAPERMILL) -k python3 -l python $(SCRIPT_DIR)/02.preprocess/preprocess_flores.ipynb /dev/null -p input_dir $(RAW_DIR)/flores_plus -p output_file $(PREP_DIR)/flores_plus.jsonl

# 03. Dataset Checking Stage
check:
	@echo "Running dataset checks notebooks..."
	$(PAPERMILL) -k python3 -l python $(SCRIPT_DIR)/03.dataset_checking/check_dataset.ipynb /dev/null -p input_file $(PREP_DIR)/flores_plus.jsonl

# 04. Benchmark Stage
benchmark:
	@echo "Running benchmarking (placeholder)..."
	# $(PAPERMILL) $(SCRIPT_DIR)/04.benchmark/benchmark.ipynb /dev/null -p input_file $(PREP_DIR)/flores_plus.jsonl

# 05. Finetune Stage
finetune:
	@echo "Running finetuning (placeholder)..."
	# $(PAPERMILL) $(SCRIPT_DIR)/05.finetune/finetune.ipynb /dev/null -p input_file $(PREP_DIR)/flores_plus.jsonl

# Clean up datasets (use with caution)
clean:
	@echo "Cleaning up datasets..."
	rm -rf $(RAW_DIR)/*
	rm -rf $(PREP_DIR)/*
