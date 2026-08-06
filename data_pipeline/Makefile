.PHONY: all download preprocess check benchmark finetune clean

-include .env
export

# Environment
PYTHON := uv run python
PAPERMILL := uv run papermill

# Directories
RAW_DIR := datasets/raw_download
PREP_DIR := datasets/preprocessed
SCRIPT_DIR := scripts

# Discover all datasets based on download scripts
DOWNLOAD_SCRIPTS := $(wildcard $(SCRIPT_DIR)/01.download/download_*.ipynb)
DATASETS := $(patsubst $(SCRIPT_DIR)/01.download/download_%.ipynb,%,$(DOWNLOAD_SCRIPTS))

# Default target runs the pipeline sequentially
all: download preprocess check benchmark finetune

# 01. Download Stage
download: $(addprefix download-, $(DATASETS))

download-%:
	@echo "Running download notebook for $*..."
	$(PAPERMILL) -k python3 -l python $(SCRIPT_DIR)/01.download/download_$*.ipynb /dev/null -p output_dir $(RAW_DIR)/$*

# 02. Preprocess Stage
PREPROCESS_SCRIPTS := $(wildcard $(SCRIPT_DIR)/02.preprocess/preprocess_*.ipynb)
PREPROCESS_DATASETS := $(patsubst $(SCRIPT_DIR)/02.preprocess/preprocess_%.ipynb,%,$(PREPROCESS_SCRIPTS))

preprocess: $(addprefix preprocess-, $(PREPROCESS_DATASETS))

preprocess-%:
	@echo "Running preprocess notebook for $*..."
	$(PAPERMILL) -k python3 -l python $(SCRIPT_DIR)/02.preprocess/preprocess_$*.ipynb /dev/null -p input_dir $(RAW_DIR)/$* -p output_file $(PREP_DIR)/$*.jsonl

# 03. Dataset Checking Stage
check:
	@echo "Running dataset checks notebooks..."
	@if [ -d "$(PREP_DIR)" ]; then \
		for file in $$(ls $(PREP_DIR)/*.jsonl 2>/dev/null); do \
			echo "Checking $$file..."; \
			$(PAPERMILL) -k python3 -l python $(SCRIPT_DIR)/03.dataset_checking/check_dataset.ipynb /dev/null -p input_file "$$file"; \
		done \
	fi

# 04. Benchmark Stage
benchmark:
	@echo "Running benchmark notebooks..."
	@if [ -d "$(SCRIPT_DIR)/04.benchmark" ]; then \
		for nb in $$(ls $(SCRIPT_DIR)/04.benchmark/*.ipynb 2>/dev/null); do \
			echo "Running $$nb..."; \
			$(PAPERMILL) -k python3 -l python "$$nb" /dev/null; \
		done \
	fi

# 05. Finetune Stage
finetune:
	@echo "Running finetuning (placeholder)..."

# Clean up datasets (use with caution)
clean:
	@echo "Cleaning up datasets..."
	rm -rf $(RAW_DIR)/*
	rm -rf $(PREP_DIR)/*
