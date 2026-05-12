# Documentation Automation and Confluence Publishing

A deterministic documentation pipeline that:

1. builds Markdown and SVG documentation from structured glossary definitions
2. synchronizes generated Markdown files to Atlassian Confluence Cloud

The system combines:

- glossary-driven document generation
- incremental documentation builds
- semantic content normalization
- deterministic Confluence synchronization
- attachment handling
- conflict detection
- versioned archive history

---

# Overview

The repository consists of two connected components:

## 1. Documentation Build System (`doc-automation`)

Builds documentation files from templates using a centralized glossary (`terms.yaml`).

Features:

- YAML-based terminology management
- automatic placeholder replacement
- Markdown and SVG processing
- incremental builds
- archive/version history
- dry-run preview mode
- restore/version inspection

---

## 2. Confluence Sync Engine (`confluence-push`)

Publishes generated Markdown files to Confluence Cloud.

Features:

- deterministic synchronization
- semantic structural diffing
- conflict detection
- attachment synchronization
- dry-run preview mode
- overwrite protection
- normalized HTML comparison

---

# Repository Structure

```text
Project structure overview:
- src/    → core Python modules
- res/    → input resources (markdown, images, SVGs)
- build/  → generated output (not versioned)
```

```text
.
├── Makefile
├── requirements.txt
├── README.md
├── LICENSE
├── confluence.yaml                  # Confluence publishing configuration
├── terms.yaml                       # Terminology and mapping definitions
├── .gitignore
│
├── src/
│   ├── doc-automation/              # Documentation generation pipeline
│   │   └── build_docs.py            # Main script to build documentation from ./res/doc-automtion/input
│   │                                # as defined in terms.yaml
│   │
│   └── confluence-push/             # Confluence publishing pipeline
│       ├── svg_converter.py         # Converts .svg to .png
│       ├── confluence_storage.py    # Handles Confluence formats and storage operations
│       └── yaml_publish.py          # Publishes content defined in confluence.yaml to Confluence
│
├── res/
│   └── doc-automation/              # Input resources for doc generation
│       ├── add/                     # Additional assets (images, figures)
│       │   └── *.png
│       └── input/                   # Source documentation files
│           ├── *.md
│           └── *.svg
│
├── build/
│   └── doc-automation/              # Generated build artifacts
│       └── output/                  # Final rendered documentation output
```

---

# Core Concept

Instead of writing raw text:

```text
The customer creates an order.
```

you write structured placeholders:

```text
The {{term:customer}} creates an {{term:order}}.
```

During the build process, placeholders are resolved using `terms.yaml`.

Generated Markdown files are then synchronized to Confluence.

This ensures:

- consistent terminology
- centralized domain language
- deterministic publishing
- reproducible documentation

---

# Installation

## Create environment and install dependencies

```bash
make install
```

This automatically:

- creates `.venv` via `venv`
- upgrades pip
- installs all dependencies


# Makefile Workflows

## Help

```bash
make help
```

## Create venv

```bash
make venv
```

## Install dependencies

```bash
make install
```

## Clean environment

```bash
    make clean
```

## Override Python

```bash
make PYTHON=/usr/bin/python3.11 install
```

---

# Build System

Note1: `make build` automatically runs `install`, which:
- creates the virtual environment if missing
- installs dependencies
- upgrades pip

Note2: all publish commands automatically ensure the virtual environment exists and dependencies are installed.


## Glossary Format (`terms.yaml`)

Example:

```yaml
terms:
  customer:
    label: Customer
    description: A person or organization that buys products

  order:
    label: Order
    description: A customer request to purchase products
```

Required fields:

- `label`
- `description`

---

# Template Syntax

## Basic usage

```text
{{term:customer}}
{{term:order}}
```

## Attribute access

```text
{{term:customer.label}}
{{term:order.description}}
```

---

# Build Commands

## Build documentation

```bash
make build
```

or

```bash
python ./src/doc-automation/build_docs.py
```

Behavior:

- processes all `.md` and `.svg` files
- replaces placeholders
- archives previous versions
- skips unchanged files
- validates glossary structure

---

## Rebuild

```bash
make rebuild
```

Behavior:
Recreate venv and rebuild docs.

---

## Dry run build

```bash
python ./src/doc-automation/build_docs.py --dry-run
```

or

```bash
python ./src/doc-automation/build_docs.py -dr
```

Behavior:

- previews changes
- shows diffs
- performs no file modifications

---

## Force build

```bash
make publish-force

```

or

```bash
python ./src/doc-automation/build_docs.py --force
```

or

```bash
python ./src/doc-automation/build_docs.py -f
```

Behavior:

- continues despite unknown terms
- inserts placeholders for unresolved terms

Example:

```text
[UNKNOWN:term]
```

---

## Restore archived version

```bash
python ./src/doc-automation/build_docs.py --restore docs/file.md
```

or

```bash
python ./src/doc-automation/build_docs.py -r docs/file.md
```

---

## List archived versions

```bash
python ./src/doc-automation/build_docs.py --multi-version-restore docs/file.md
```

or

```bash
python ./src/doc-automation/build_docs.py -R docs/file.md
```

---

# Archive System

Before modification, files are archived to:

```text
build/doc-automation/archive/
```

Example:

```text
archive/docs/api/
  20260410_142301_123456_order.md
  20260410_150012_654321_order.md
```

Features:

- preserved folder structure
- timestamped backups
- full rollback history

---

# Incremental Builds

The build system only processes changed files using:

- file hash comparison
- cached build state
- glossary change detection

Cache file:

```text
build/doc-automation/.build_cache.json
```

---

# Confluence Synchronization

## Environment Variables

Create a `.env` file:

```env
CONFLUENCE_BASE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token
```

---

# Confluence YAML Configuration

Example `confluence.yaml`:

```yaml
pages:
  - id: "1413054556"
    file: "build/doc-automation/output/example.md"

    attachments:
      diagram.svg:
        path: "./build/doc-automation/output/diagram.svg"
        caption: "Architecture diagram"
```

---

# Confluence Commands

## Publish normally

```bash
make publish
```

or

```bash
python ./src/confluence-push/yaml_publish.py confluence.yaml
```

---

## Dry run

```bash
make publish-dry
```

or

```bash
python ./src/confluence-push/yaml_publish.py confluence.yaml --dry-run
```

---

## Force overwrite

```bash
make publish-force
```

or

```bash
python ./src/confluence-push/yaml_publish.py confluence.yaml --force
```

---

# Combined Workflow Commands

## Build documentation only

```bash
make build
```

Runs:

```bash
python ./src/doc-automation/build_docs.py
```

---

## Build and publish

```bash
make all
```

Runs:

1. documentation build
2. Confluence publish

Equivalent to:

```bash
make build
make publish
```

---

## Build and force publish

```bash
make all-force
```

Runs:

1. documentation build
2. forced Confluence overwrite

Equivalent to:

```bash
make build
make publish-force
```

---

# Change Detection

The synchronization engine performs semantic structural comparison.

Pipeline:

```text
Markdown
↓
HTML conversion
↓
normalization
↓
block extraction
↓
remote normalization
↓
semantic comparison
```

Compared block types:

- headings (`h1–h4`)
- paragraphs (`p`)
- list items (`li`)
- table cells (`td`, `th`)

Ignored differences:

- whitespace
- Confluence editor formatting noise
- serialization artifacts
- paragraph/list duplication

---

# Diff Behavior

Dry-run and conflict detection display semantic diffs:

```diff
--- confluence
+++ local
```

The system compares normalized structure instead of raw HTML.

---

# Conflict Handling

A conflict occurs when:

- remote normalized content differs from local normalized content

Behavior:

1. warning is displayed
2. semantic diff is shown
3. explicit confirmation is required

No silent overwrites occur.

---

# Attachment Handling

Attachments use marker syntax:

```text
@attach diagram.svg
```

or

```text
@attach diagram.svg | Architecture diagram
```

Features:

- uploaded only when content changes
- deterministic naming via content hash
- SVG → PNG conversion
- attachment reuse when identical

---

# State Handling

Synchronization state is stored locally:

```text
build/confluence-push/.state.json
```

Example:

```json
{
  "1413054556": {
    "hash": "abcdef123456"
  }
}
```

The system does not rely on Confluence page properties.

---

# Validation Rules

The glossary validator checks:

- required root keys
- required fields
- field types
- unknown references

Strict validation is enabled by default.

---

# Supported Formats

Build system:

- Markdown (`.md`)
- SVG (`.svg`)

Confluence synchronization:

- Markdown pages
- image attachments

---

# Architecture

```text
terms.yaml
↓
placeholder resolution
↓
Markdown/SVG processing
↓
archive creation
↓
incremental build
↓
generated Markdown
↓
Confluence normalization pipeline
↓
semantic diff
↓
conflict handling
↓
Confluence update
```

---

# Design Philosophy

- local files are the source of truth
- comparisons must be structural, not textual
- deterministic output is preferred over formatting preservation
- automation should be safe and inspectable
- explicit conflicts are preferred over silent divergence

---

# Summary

This repository provides a deterministic documentation pipeline with:

- centralized glossary management
- automated document generation
- incremental builds
- archive/version history
- semantic Confluence synchronization
- conflict-safe publishing
- reproducible documentation output
