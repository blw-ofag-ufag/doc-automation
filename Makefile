VENV=.venv
PY=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

# -------------------------------------------------------
# VENV SETUP
# -------------------------------------------------------

venv:
	@test -d $(VENV) || python -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip

# -------------------------------------------------------
# INSTALL
# -------------------------------------------------------

install: venv
	$(PIP) install -r requirements.txt

# -------------------------------------------------------
# BUILD DOCS
# -------------------------------------------------------

build: venv
	$(PY) ./src/doc-automation/build_docs.py

complete: build run

forcedbuild: build force

# -------------------------------------------------------
# RUN MODES
# -------------------------------------------------------

run: venv
	$(PY) src/confluence-push/yaml_publish.py confluence.yaml

dry: venv
	$(PY) src/confluence-push/yaml_publish.py confluence.yaml --dry-run

force: venv
	$(PY) src/confluence-push/yaml_publish.py confluence.yaml --force

# -------------------------------------------------------
# HELP
# -------------------------------------------------------

help:
	@echo "Available commands:"
	@echo ""
	@echo "  make venv        : create virtual environment (.venv)"
	@echo "  make install     : install dependencies into venv"
	@echo "  make build       : generate markdown docs"
	@echo "  make complete    : build docs and publish normally"
	@echo "  make forcedbuild : build docs and force publish"
	@echo "  make run         : publish to Confluence (normal run)"
	@echo "  make dry         : show diff only (no changes applied)"
	@echo "  make force       : force overwrite Confluence page"
	@echo ""