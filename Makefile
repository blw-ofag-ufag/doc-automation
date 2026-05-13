# =======================================================
# PORTABLE PYTHON / VENV CONFIG
# =======================================================

VENV ?= .venv

# Prefer python3, fallback to python
PYTHON ?= $(shell command -v python3 || command -v python)

# Cross-platform virtualenv paths
ifeq ($(OS),Windows_NT)
    PY := $(VENV)/Scripts/python.exe
    PIP := $(VENV)/Scripts/pip.exe
else
    PY := $(VENV)/bin/python
    PIP := $(VENV)/bin/pip
endif

# Default target
.DEFAULT_GOAL := help

# =======================================================
# PHONY TARGETS
# =======================================================

.PHONY: help check-python \
        venv install clean \
        build build-force rebuild \
        publish publish-dry publish-force \
        all all-force

# =======================================================
# PYTHON / VENV SETUP
# =======================================================

check-python:
	@command -v $(PYTHON) >/dev/null 2>&1 || \
		(echo "ERROR: Python interpreter not found."; exit 1)

venv: check-python
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	$(PY) -m pip install --upgrade pip

# Install project dependencies
install: venv
	$(PIP) install -r requirements.txt

# =======================================================
# CLEANUP
# =======================================================

clean:
	rm -rf $(VENV)
	rm -rf build/doc-automation/output
	rm -f build/doc-automation/.build_cache.json

# =======================================================
# BUILD DOCS
# =======================================================

# Build requires dependencies
build: install
	@echo "Running build_docs.py"
	$(PY) ./src/doc-automation/build_docs.py

# Force rebuild docs
build-force: install
	@echo "Running build_docs.py --force"
	$(PY) ./src/doc-automation/build_docs.py --force

# Recreate venv and rebuild docs
rebuild: clean build

# =======================================================
# CONFLUENCE PUBLISH
# =======================================================

publish: install
	$(PY) src/confluence-push/yaml_publish.py confluence.yaml

publish-dry: install
	$(PY) src/confluence-push/yaml_publish.py \
		confluence.yaml --dry-run

publish-force: install
	$(PY) src/confluence-push/yaml_publish.py \
		confluence.yaml --force

# =======================================================
# COMBINED WORKFLOWS
# =======================================================

# Build docs + publish normally
all: build publish

# Build docs + force publish
all-force: build-force publish-force

# =======================================================
# HELP
# =======================================================

help:
	@echo ""
	@echo "Available commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make venv           Create virtual environment"
	@echo "  make install        Install dependencies"
	@echo ""
	@echo "Build:"
	@echo "  make build          Generate markdown docs"
	@echo "  make build-force    Force rebuild"
	@echo "  make rebuild        Recreate venv and rebuild docs"
	@echo ""
	@echo "Publish:"
	@echo "  make publish        Publish to Confluence"
	@echo "  make publish-dry    Dry-run only"
	@echo "  make publish-force  Force overwrite pages"
	@echo ""
	@echo "Workflows:"
	@echo "  make all            Build docs and publish"
	@echo "  make all-force      Force build + publish"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean          Remove venv + build artifacts"
	@echo ""