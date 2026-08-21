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

Python 3.9 is the minimum supported runtime. Ordinary CI exercises the keyless preflight on that baseline.

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

## Keyless preflight

Before any provider-backed compile, run the local structural preflight:

```bash
make check
```

`make check` requires no API key, running model service, or provider package. It checks Python syntax and helper imports, validates shell syntax, renders a prompt from a tiny synthetic test fixture, and runs the local regressions for prompt contracts, failure routing, target composition, review orchestration, build-directory isolation, and successful artefact sanity.

Provider connectivity/configuration checks remain explicit and separate:

```bash
make check-ollama
make openai-check
```

`check-ollama` contacts the configured local Ollama service. `openai-check` performs a real OpenAI API request and may incur usage charges, so run it only intentionally. Neither is part of `make check` or ordinary CI.

The self-example compile is a separate integration acceptance step because it actually executes the configured model pipeline.

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

Peer review has a small machine-readable status contract:

* `PASS` — no findings; `revise.tex` is promoted deterministically to `final.tex` with no extra model call.
* `REVISE_REALISATION` — only wording/presentation findings; one bounded final realisation-revision pass is permitted.
* `BLOCKED_SOURCE` — at least one conceptual/source defect; compilation stops before final revision and writes a diagnostic under `build/errors/`.

Malformed or internally inconsistent review status also fails closed. Peer review never amends `outline.md`, supplies missing citations as authority, or triggers a review/revision loop.

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
* Peer review output is diagnostic and emitted as structured Markdown.
* Determinism depends on backend support for fixed seeds and low temperature settings.

---

## CI, paid compilation, and the self-example

Ordinary CI is deliberately **keyless**. Pushes and pull requests run `make check` on Python 3.9, and the normal CI workflow does not reference provider credentials or make model calls.

Paid API compilation is a separate manual operation. `.github/workflows/publish-self-example.yml` has only a `workflow_dispatch` trigger, requires an explicit paid-usage checkbox, is restricted to `main`, and permits the paid job only when the dispatcher is the repository owner. It also places the provider call inside the `paid-compilation` GitHub Environment. Repository tests enforce that separation.

A successful approved run builds an inspectable self-example site in `docs/` inside the workflow runner and deploys it through GitHub Pages Actions. The site includes the rendered final essay, the authoritative outline, peer-review diagnostics, raw stage artefacts, and provenance metadata. Generated prose is not committed back into the source tree.

Recommended repository configuration:

1. In **Settings → Environments**, create `paid-compilation`, require the repository owner as reviewer, and restrict deployment branches to `main`. If you are the sole reviewer, do not enable “prevent self-review”.
2. Prefer moving `OPENAI_API_KEY` from a repository secret to an environment secret of the same name under `paid-compilation`. Environment secrets are unavailable until the environment approval passes.
3. In **Settings → Pages**, set the publishing source to **GitHub Actions**. Do not configure branch-based `main / docs`; Actions commits made with `GITHUB_TOKEN` do not trigger that Pages build path.
4. To publish, open **Actions → Compile and publish self-example → Run workflow**, explicitly authorize the paid compilation, then approve the `paid-compilation` environment job.

One approved successful publication invokes the configured provider for draft, smooth, revise, and peer review. It invokes the provider once more only when peer review returns `REVISE_REALISATION`; `PASS` finalisation is deterministic and `BLOCKED_SOURCE` stops before a final provider call. The workflow currently caps each model-backed stage at 20,000 output tokens and performs no automatic retry.

---

## Project intent

This repository is both an essay and a worked example of **compiled prose**:

* specification and execution are explicitly separated
* prose is reproducible and retargetable
* authorship is located upstream in structure, not surface realisation

The build system is intentionally minimal and transparent.
