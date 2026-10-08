.PHONY: all preflight download preprocess check test

# Thin wrapper around run_pipeline.py, which does preflight checks, runs each
# stage, validates its outputs and skips stages that are already up to date.
RUN := uv run python run_pipeline.py

all:
	$(RUN)

preflight:
	$(RUN) --preflight-only

download:
	$(RUN) --only 01

preprocess:
	$(RUN) --only 02

check:
	$(RUN) --only 03

test:
	uv run pytest tests -q
