.PHONY: all download preprocess check benchmark finetune clean

# Environment
PYTHON := uv run python

# Directories
RAW_DIR := datasets/raw_download
PREP_DIR := datasets/preprocessed
SCRIPT_DIR := scripts

# Default target runs the pipeline sequentially (for testing purposes)
all: download preprocess check benchmark finetune

# 01. Download Stage
download:
	@echo "Running download scripts..."
	$(PYTHON) $(SCRIPT_DIR)/01.download/download_flores.py --output $(RAW_DIR)/flores_plus

# 02. Preprocess Stage
preprocess:
	@echo "Running preprocess scripts..."
	$(PYTHON) $(SCRIPT_DIR)/02.preprocess/preprocess_flores.py --input $(RAW_DIR)/flores_plus --output $(PREP_DIR)/flores_plus.jsonl

# 03. Dataset Checking Stage
check:
	@echo "Running dataset checks..."
	$(PYTHON) $(SCRIPT_DIR)/03.dataset_checking/check_dataset.py --input $(PREP_DIR)/flores_plus.jsonl

# 04. Benchmark Stage
benchmark:
	@echo "Running benchmarking (placeholder)..."
	# $(PYTHON) $(SCRIPT_DIR)/04.benchmark/benchmark.py --input $(PREP_DIR)/flores_plus.jsonl

# 05. Finetune Stage
finetune:
	@echo "Running finetuning (placeholder)..."
	# $(PYTHON) $(SCRIPT_DIR)/05.finetune/finetune.py --input $(PREP_DIR)/flores_plus.jsonl

# Clean up datasets (use with caution)
clean:
	@echo "Cleaning up datasets..."
	rm -rf $(RAW_DIR)/*
	rm -rf $(PREP_DIR)/*
