# Introduction

This essay concerns academic and technical writing: forms of prose whose primary function is the reliable transmission of concepts, arguments, and procedures. In these contexts, clarity is primal. Expressive gesture is not merely optional but often counterproductive—at best introducing noise, and at worst functioning as borrowed weight, rhetorical camouflage, or obfuscation. The essay proposes compiled prose as a model in which conceptual structure is authored explicitly and upstream, while natural language is treated as a compiled artefact rather than a site of primary expression. In this model, the detailed outline functions as source code, encoding the logic, dependencies, and invariants of the argument; prose becomes machine code, a deterministic rendering optimised for legibility and compatibility with disciplinary norms, institutional conventions, and reader expectations. This is not a claim that prose is unimportant, nor that meaning is fully reducible to structure, nor that expressive writing is obsolete. It is a claim about separation of concerns: in domains where misunderstanding carries real epistemic or material cost, treating style, voice, and register as externalised constraints—akin to compilation targets or stylesheets—improves reproducibility, auditability, and revision without erasing conceptual authorship. The essay is descriptive rather than prescriptive. It names a practice already emerging, often implicitly and unevenly, under the pressures of scale, collaboration, and AI-assisted execution, and asks what follows if we acknowledge it explicitly rather than continuing to treat linguistic execution as a sacred site of authorship.


# Build & Installation Guide

This repository implements a **make-based compilation pipeline for prose**. Conceptual structure is treated as source code; prose is treated as a compiled artefact. The system supports either a **local model backend (Ollama)** or the **OpenAI API**, selectable via configuration.

---

## Prerequisites (all modes)

You will need:

* **GNU Make**
* **Bash**
* **Python ≥ 3.9**
* **curl**

Optional but recommended:

* `jq` (for JSON handling with Ollama)

### Installing prerequisites

**Debian / Ubuntu**

```bash
sudo apt install make python3 curl jq
```

**macOS (Homebrew)**

```bash
brew install make python curl jq
```

---

## Clone the repository

```bash
git clone <repo-url>
cd <repo-name>
```

---

## Configuration

Copy the example environment file and edit as required:

```bash
cp .env.example .env
```

The `.env` file controls:

* backend selection (`ollama` or `openai`)
* model choice
* temperature and seed
* target style (journal / venue)

The `.env` file is **not committed**.

To load it into your shell:

```bash
set -a
source .env
set +a
```

---

## Option A: Local backend (Ollama)

### Install Ollama

Follow instructions at:

[https://ollama.com](https://ollama.com)

Pull a model (example):

```bash
ollama pull llama3.1
```

Ensure the Ollama service is running:

```bash
ollama serve
```

### Configure `.env`

```bash
BACKEND=ollama
OLLAMA_MODEL=llama3.1
OLLAMA_HOST=http://localhost:11434
```

No Python packages are required for this mode.

---

## Option B: OpenAI API backend (cloud)

> **Note:** ChatGPT Plus does **not** include API access. API usage requires a separate OpenAI developer account and billing.

### 1. Create an API key

Create an API key at:

[https://platform.openai.com/](https://platform.openai.com/)

Add it to `.env`:

```bash
OPENAI_API_KEY=sk-...
```

### 2. Install Python dependency

Create a virtual environment (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure `.env`

```bash
BACKEND=openai
OPENAI_MODEL=gpt-5
OPENAI_TEMPERATURE=0.2
OPENAI_SEED=42
```

---

## Running the pipeline

Build the full essay:

```bash
make final
```

Run individual stages:

```bash
make draft
make smooth
make revise
make review
make final
```

Generated artefacts appear in `build/`:

* `draft.tex`
* `smooth.tex`
* `revise.tex`
* `peer_review.md`
* `final.tex`

---

## Switching backends

Override the backend at runtime:

```bash
make BACKEND=ollama final
make BACKEND=openai final
```

Switch target style (journal / venue):

```bash
make TARGET_STYLE=prompts/targets/<journal>.md final
```

---

## Notes on reproducibility

* The **authoritative sources** are `outline.md` and the prompt files in `prompts/`.
* LaTeX outputs are treated as compiled artefacts.
* Peer review output is diagnostic and emitted as Markdown.
* Determinism depends on backend support for fixed seeds and low temperature settings.

---

## Project intent

This repository is both an essay and a worked example of **compiled prose**:

* specification and execution are explicitly separated
* prose is reproducible and retargetable
* authorship is located upstream in structure, not surface realisation

The build system is intentionally minimal and transparent.
