# Compiled Prose

Compiled Prose is a small, file-driven compiler pipeline for academic and technical prose. The human-authored source carries the claims, argument, structure, evidence, citations, and unresolved choices. Model-backed stages realise that source as prose for a selected target, but their outputs remain derived artefacts rather than new conceptual authority.

The compiler analogy is architectural, not a promise of byte-for-byte deterministic generation. The project aims for a predictable, auditable transformation process whose authority and failure rules are stable even when model output varies.

## Canonical documentation

The repository deliberately keeps its documentation authority surface small:

- `README.md` — project concept, setup, quick start, and release-facing operation;
- `pipeline.md` — normative pipeline semantics and the boundary between mechanically enforced rules, prompt contracts, and design constraints;
- `prompts/*.md` and `prompts/targets/*.md` — executable stage and target contracts;
- `outline.md` — the authored conceptual source for the repository's self-example, not compiler documentation.

Generated artefacts, source-audit evidence, and diagnostics are outputs or evidence about compilation, not authorities for what the source says.

## Architecture

A stage is assembled as one flattened prompt before the backend is invoked:

```text
system contract
  + stage contract
  + target requirements
  + authoritative source
  + derived stage input, when distinct from the source
  + diagnostic context, when applicable
  + output/failure contract
        |
        v
model backend
        |
        v
backend-independent protocol enforcement
        |
        +--> build/<stage artefact>
        `--> build/errors/<stage>.md
```

The original authoritative source is carried alongside downstream derived artefacts. Target files constrain realisation for a venue or audience; they do not supply claims, evidence, citations, examples, or scope. Peer review is diagnostic and likewise cannot become conceptual authority.

See `pipeline.md` for the exact stage and failure semantics.

# Build & Installation Guide

## Prerequisites

You need:

- GNU Make
- Bash
- Python >= 3.9
- `curl`

`jq` is optional. Python 3.9 is the minimum runtime exercised by ordinary CI.

For release-candidate LaTeX validation of the self-example, also install `latexmk` and a working LaTeX distribution. Publication additionally uses `pandoc` to build the inspectable Pages site.

For Debian/Ubuntu:

```bash
sudo apt install make python3 curl jq latexmk texlive-latex-extra pandoc
```

For macOS with Homebrew:

```bash
brew install make python curl jq pandoc
```

A TeX distribution that provides `latexmk` (for example MacTeX) is also required on macOS for PDF validation.

## Configuration

Copy the example environment file and edit it as required:

```bash
cp .env.example .env
set -a
source .env
set +a
```

`.env` is not committed. It selects the backend, model configuration, and target style.

### Local backend: Ollama

Install Ollama, pull a model, and ensure its service is running. A typical configuration is:

```bash
BACKEND=ollama
OLLAMA_MODEL=llama3.1
OLLAMA_HOST=http://localhost:11434
```

### OpenAI API backend

ChatGPT subscriptions do not include API usage. OpenAI API compilation requires a separately billed API account and key.

For the OpenAI backend, install the Python dependency in a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then configure, for example:

```bash
BACKEND=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5
OPENAI_TEMPERATURE=0.2
OPENAI_SEED=42
```

## Keyless preflight

Run the provider-free structural and regression suite before any model-backed compile:

```bash
make check
```

`make check` performs Python and shell syntax checks, runs the local unit/smoke tests, and audits the repository self-example's citation/source bookkeeping. It requires no API key, provider package, running model service, or network access.

The self-example source audit can also be run directly:

```bash
make self-preflight
```

This checks that every source citation in `outline.md` has a catalog entry, every catalog entry has dated verification evidence in `self-example/source-audit.json`, no unverified/extra source entry is present, and the disposable entropy fixture has not been promoted into the release source tree. The audit file is release-readiness evidence only; it is not passed to model stages and does not add conceptual authority beyond `outline.md`.

Provider connectivity checks are deliberately separate:

```bash
make check-ollama
make openai-check
```

`check-ollama` contacts the configured local Ollama service. `openai-check` makes a real OpenAI API request and may incur a charge; it is never part of `make check` or ordinary CI.

## Running the pipeline

The repository self-example has one obvious end-to-end command:

```bash
make self
```

`make self` first runs the keyless source preflight, deletes the transient build directory, compiles `outline.md` through the normal pipeline using the selected backend, rejects non-authoritative explicit citation labels that can be checked mechanically, and then requires `latexmk` to produce `build/final.pdf`. It does not hide or bypass the ordinary stage contracts. If `BACKEND=openai` is selected, the command makes paid API calls; no paid invocation is part of the keyless preflight.

For generic compilation, `IN` names the authoritative conceptual source and is required for a fresh model-backed build:

```bash
make final IN=outline.md
```

Run individual stages with the same source explicitly supplied:

```bash
make draft IN=outline.md
make smooth IN=outline.md
make revise IN=outline.md
make review IN=outline.md
make final IN=outline.md
```

There is also an independent summary transform:

```bash
make summarize IN=outline.md
```

By default generated files live under `build/`:

- `build/draft.tex`
- `build/smooth.tex`
- `build/revise.tex`
- `build/peer_review.md`
- `build/final.tex`
- `build/final.pdf` after successful self-example LaTeX validation
- `build/summary.tex` when `summarize` is requested
- `build/errors/<stage>.md` for blocking diagnostics

The build root is configurable without changing source paths:

```bash
make BUILD_DIR=/tmp/compiled-prose final IN=outline.md
```

`make validate-latex` validates an already-existing `build/final.tex` and produces `build/final.pdf`; it fails if `final.tex` is absent rather than implicitly invoking a model-backed pipeline. `make clean` removes the known generated artefacts and diagnostics from the selected build directory. `make clobber` removes that build directory entirely.

## Peer-review gate

Peer review uses a small machine-readable status contract:

- `PASS` — no findings; `revise.tex` is copied exactly to `final.tex` without another model call.
- `REVISE_REALISATION` — findings are realisation-only; exactly one bounded final realisation pass is permitted.
- `BLOCKED_SOURCE` — at least one finding requires authorial source work; compilation stops before final revision and emits an external diagnostic.

Malformed or internally inconsistent review status also fails closed. The review can identify missing support, but it cannot amend the source or turn a suggested citation into authority.

## Self-example release acceptance

Mechanical checks deliberately stop short of claiming semantic equivalence. After a successful self-compilation, a human must compare the candidate final essay with `outline.md` and confirm that no material claim was introduced without source authority, no proposition was silently strengthened or weakened, no example/theory/citation/historical claim was added downstream, every source-supplied citation remains present and attached to the claim it supports, peer review did not expand scope, and important qualifications and uncertainty were preserved.

The publication workflow exposes that review as an `acceptance.html` checklist in the candidate bundle. Configure the `github-pages` GitHub Environment with the repository owner as a required reviewer. The compile job uploads `self-example-candidate-<source-sha>` before the deployment job reaches that environment, allowing the candidate to be inspected before Pages publication is approved. A failed semantic check goes back to `outline.md` for a source defect or to the compiler/prompt layer for a compiler defect; conceptual content must not be hand-patched into generated prose.

## Retained self-example artefacts

`build/` remains transient and generated prose is not committed to the source tree. The canonical current worked-example evidence is the accepted Pages deployment and its inspectable candidate bundle. It contains:

- the authoritative `outline.md`;
- dated `source-audit.json` evidence for the supplied references;
- draft, smooth, and revise stage artefacts;
- the final peer-review report;
- final generated LaTeX;
- the PDF produced by the documented LaTeX toolchain;
- source commit, model, target, workflow-run metadata, and the human acceptance checklist.

The workflow also retains the candidate as a normal Actions artifact for 90 days so the exact pre-deployment bundle can be inspected independently of Pages. The Pages `build.json` records the source commit and workflow run. None of these downstream artefacts becomes conceptual authority, and no secret or provider state is retained.

## Switching backend or target

Runtime overrides remain explicit:

```bash
make BACKEND=ollama final IN=outline.md
make BACKEND=openai final IN=outline.md
make TARGET_STYLE=prompts/targets/journal_academic.md final IN=outline.md
```

A target controls acceptable realisation for the audience or venue. It is not permission to invent content that is absent from the authoritative source.

## Reproducibility

Compiled Prose targets semantic and specification-level reproducibility:

- source, prompts, target requirements, stage order, protocol checks, and configuration are file-driven and inspectable;
- the same authority boundaries and failure rules apply across supported backends;
- a `PASS` review produces an exact deterministic promotion from `revise.tex` to `final.tex`;
- model-generated prose is **not** promised to be byte-for-byte identical across runs, models, provider versions, or platforms, even when a backend accepts a seed.

Seeds and low temperatures can reduce variance where supported, but they are configuration controls rather than a repository-wide determinism guarantee.

## CI, paid compilation, and the self-example

Ordinary CI is deliberately keyless. Pushes and pull requests run `make check` and do not reference provider credentials or make model calls.

Paid self-example compilation is a separate manual publication path in `.github/workflows/publish-self-example.yml`. It has only a `workflow_dispatch` trigger, requires explicit paid-use authorization, is restricted to `main`, and places the provider call behind the `paid-compilation` GitHub Environment. A successful approved run executes `make self`, builds the inspectable candidate bundle, and waits at the separately protected `github-pages` environment before deployment; generated prose is not committed to the source tree.

Recommended repository configuration:

1. Create the `paid-compilation` environment, require the repository owner as reviewer, and restrict it to `main`.
2. Store `OPENAI_API_KEY` as an environment secret under `paid-compilation` rather than exposing it to ordinary CI.
3. Configure GitHub Pages to publish from **GitHub Actions**.
4. Configure the `github-pages` environment to require the repository owner as reviewer, so the compiled candidate can be adversarially checked before deployment.
5. Start publication manually from **Actions -> Compile and publish self-example -> Run workflow**, explicitly authorize paid compilation, approve the `paid-compilation` environment, inspect the uploaded acceptance candidate after compilation, and approve `github-pages` only if the source-authority checklist passes.

One approved successful compilation invokes the configured provider for draft, smooth, revise, and peer review. It makes one additional provider call only when review returns `REVISE_REALISATION`; `PASS` finalisation is deterministic and `BLOCKED_SOURCE` stops before a final provider call. The workflow currently caps each model-backed stage at 20,000 output tokens and performs no automatic retry.

## Project intent

This repository is both an implementation and its own worked example. Its central separation of concerns is simple: humans author the conceptual source; compiler stages realise it under explicit constraints; generated prose and diagnostics remain inspectable downstream artefacts.
