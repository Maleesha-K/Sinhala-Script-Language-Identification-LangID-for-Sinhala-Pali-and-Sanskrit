.PHONY: all download preprocess check benchmark finetune clean


-include .env
export

# Environment
PYTHON := uv run python
PAPERMILL := uv run papermill
export HF_HUB_DISABLE_SYMLINKS := 1

ifeq ($(OS),Windows_NT)
    DEV_NULL := NUL
    CONLID_PYTHON := $(CONLID_VENV)/Scripts/python
else
    DEV_NULL := /dev/null
    CONLID_PYTHON := $(CONLID_VENV)/bin/python
endif




# Directories
RAW_DIR := datasets/raw_download
PREP_DIR := datasets/preprocessed
SCRIPT_DIR := scripts

# Discover all datasets based on download scripts
DOWNLOAD_SCRIPTS := $(wildcard $(SCRIPT_DIR)/01.download/download_*.ipynb)
DATASETS := $(patsubst $(SCRIPT_DIR)/01.download/download_%.ipynb,%,$(DOWNLOAD_SCRIPTS))

# Default target runs the pipeline sequentially
all: download preprocess check benchmark finetune benchmark-finetuned

# 01. Download Stage
download: $(addprefix download-, $(DATASETS))

download-%:
	@echo "Running download notebook for $*..."
	$(PAPERMILL) -k python3 -l python $(SCRIPT_DIR)/01.download/download_$*.ipynb $(DEV_NULL) -p output_dir $(RAW_DIR)/$*

# 02. Preprocess Stage
PREPROCESS_SCRIPTS := $(wildcard $(SCRIPT_DIR)/02.preprocess/preprocess_*.ipynb)
PREPROCESS_DATASETS := $(patsubst $(SCRIPT_DIR)/02.preprocess/preprocess_%.ipynb,%,$(PREPROCESS_SCRIPTS))

preprocess: $(addprefix preprocess-, $(PREPROCESS_DATASETS))

preprocess-%:
	@echo "Running preprocess notebook for $*..."
	$(PAPERMILL) -k python3 -l python $(SCRIPT_DIR)/02.preprocess/preprocess_$*.ipynb $(DEV_NULL) -p input_dir $(RAW_DIR)/$* -p output_file $(PREP_DIR)/$*.jsonl

# 03. Dataset Checking Stage
check:
	@echo "Running dataset checks notebooks..."
	$(PAPERMILL) -k python3 -l python $(SCRIPT_DIR)/03.dataset_checking/check_dataset.ipynb $(DEV_NULL) -p input_dir $(PREP_DIR)

# 04. Benchmark Stage
CONLID_DIR = models/benchmark/ConLID
CONLID_REPO = $(CONLID_DIR)/repo
CONLID_VENV = $(CONLID_DIR)/.venv

setup-conlid:
	@echo "Setting up ConLID environment..."
	$(PYTHON) -c "import os, subprocess; os.makedirs('$(CONLID_DIR)', exist_ok=True); subprocess.run(['git', 'clone', 'https://github.com/epfl-nlp/language-identification.git', '$(CONLID_REPO)']) if not os.path.exists('$(CONLID_REPO)') else None"
	uv venv $(CONLID_VENV)
	uv pip install --python $(CONLID_VENV) -r $(CONLID_REPO)/requirements.txt
	uv pip install --python $(CONLID_VENV) ipykernel
	$(CONLID_PYTHON) -m ipykernel install --user --name=conlid-venv --display-name "Python (ConLID Benchmark)"
	@echo "ConLID setup complete! Kernel 'conlid-venv' is now available."

benchmark:
	@echo "Running benchmark notebooks..."
	$(PYTHON) -c "import os, glob, subprocess, sys, jupyter_client; \
	bdir = '$(SCRIPT_DIR)/04.benchmark'; \
	(not os.path.exists(bdir)) or [ \
		(print(f'Running {nb}...'), \
		(sys.exit(1) if (os.path.basename(nb) == 'ConLID.ipynb' and 'conlid-venv' not in jupyter_client.kernelspec.KernelSpecManager().find_kernel_specs() and (print('Kernel \'conlid-venv\' not found. Please run \'make setup-conlid\' first.') or True)) else None), \
		subprocess.run(['uv', 'run', 'papermill', '-k', ('conlid-venv' if os.path.basename(nb) == 'ConLID.ipynb' else 'python3'), '-l', 'python', nb, '$(DEV_NULL)'], check=True) \
		) for nb in glob.glob(os.path.join(bdir, '*.ipynb')) \
	]"

# 05. Finetune Stage
finetune: finetune-dataset finetune-models

finetune-dataset:
	@echo "Running fine-tuning dataset setup..."
	@if [ -d "$(SCRIPT_DIR)/05.finetune_dataset" ]; then \
		for nb in $$(ls $(SCRIPT_DIR)/05.finetune_dataset/*.ipynb 2>/dev/null); do \
			echo "Running $$nb..."; \
			$(PAPERMILL) -k python3 -l python "$$nb" /dev/null; \
		done \
	fi

finetune-models:
	@echo "Running fine-tuning models..."
	@if [ -d "$(SCRIPT_DIR)/06.finetune_models" ]; then \
		for nb in $$(ls $(SCRIPT_DIR)/06.finetune_models/*.ipynb 2>/dev/null); do \
			echo "Running $$nb..."; \
			$(PAPERMILL) -k python3 -l python "$$nb" /dev/null; \
		done \
	fi

# 07. Benchmark Finetuned Models Stage
benchmark-finetuned:
	@echo "Running fine-tuned benchmark notebooks..."
	@if [ -d "$(SCRIPT_DIR)/07.benchmark_finetuned" ]; then \
		for nb in $$(ls $(SCRIPT_DIR)/07.benchmark_finetuned/*.ipynb 2>/dev/null); do \
			echo "Running $$nb..."; \
			$(PAPERMILL) -k python3 -l python "$$nb" /dev/null; \
		done \
	fi

# Clean up datasets (use with caution)
clean:
	@echo "Cleaning up datasets..."
	rm -rf $(RAW_DIR)/*
	rm -rf $(PREP_DIR)/*
