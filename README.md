# Compiled Prose

Compiled Prose is a small, file-driven compiler pipeline for academic and technical prose. The human-authored source carries the claims, argument, conceptual structure, evidence, citations, attributions, and unresolved choices. Model-backed stages realise that source as prose for a selected target, but their outputs remain derived artefacts rather than new conceptual authority.

The compiler analogy is architectural, not a promise of byte-for-byte deterministic generation. The project aims for a predictable, auditable transformation process whose authority and failure rules are stable even when model output varies.

## Published example

The repository publishes its own compiled essay as a worked example: [view it on GitHub Pages](https://grantaj.github.io/compiled-prose/). The site makes `outline.md` a first-class view and can present several target renderings of the same source side-by-side. The initial public targets are `journal_academic`, `magazine_general`, and `explain_like_im_5`. They are audience/genre contracts, not quality levels.

## Canonical documentation

- `README.md` — project concept, setup, quick start, and release operation;
- `pipeline.md` — normative pipeline semantics and enforcement boundaries;
- `prompts/*.md` and `prompts/targets/*.md` — executable stage and target contracts;
- `outline.md` — the authored conceptual source for the repository example.

Generated artefacts, source-audit evidence, bibliography metadata, and diagnostics are outputs or evidence about compilation, not authorities for what the source says.

## Architecture

The core publication graph is deliberately small:

```text
authoritative source
      |
      v
   REALISE
      |
      v
 PEER REVIEW
   /    |     \
 PASS  REVISE  BLOCKED_SOURCE
  |      |          |
  |      v          `--> diagnostic + stop
  |   FINAL REVISION
  |      |
  +------+
      |
      v
   final.tex
```

A second writing pass happens only when peer review supplies new diagnostic information that justifies it. `PASS` promotes `realise.tex` directly to `final.tex`; `REVISE_REALISATION` permits exactly one bounded final revision; `BLOCKED_SOURCE` returns control to the human-authored source.

This simplification is motivated by strong regression evidence rather than a claim that every model or document behaves identically. In a recent GPT-5.6 Sol compilation of the `grantaj/censorship` regression case, the old draft-to-smooth pass left about 99.42% of words unchanged and smooth-to-revise left about 99.86% unchanged, while the two passes cost roughly $0.73. They also failed to repair the main structural weakness that had motivated them: journal prose remaining too close to a prosified outline. Peer review, by contrast, added genuinely new information and exposed substantive source and literature problems. Modern models are therefore asked to produce a strong complete first realisation, peer review remains the independent second look, and another writing call is conditional on actual review findings.

### Prompt composition and authority

A model-backed stage is assembled as one flattened prompt:

```text
system contract
  + stage contract
  + target requirements
  + authoritative source
  + optional bibliographic rendering metadata
  + derived stage input, when distinct from the source
  + peer-review diagnostic context, for final revision only
  + output/failure contract
        |
        v
model backend
        |
        v
backend-independent protocol enforcement
```

The original authoritative source is carried alongside any downstream derived artefact. The source alone supplies conceptual content and topology. Target files constrain audience, register, coverage/compression, rhetorical form, formatting, and evidence/attribution/citation presentation. They do not supply claims, evidence, citations, attributions, content-bearing examples, or conceptual scope.

Coverage is exhaustive by default, but a target may explicitly permit summarisation, compression, or selective omission. Presentation topology is not authoritative by default: source bullets, heading depth, adjacency, and navigation order may be reorganised when conceptual topology permits. Genuine dependency, procedure, chronology, taxonomy, qualification scope, and support attachment remain authoritative.

A target may explicitly permit non-authoritative illustrative scaffolding to explain source-authorised concepts, but that scaffolding must remain traceable and removable and cannot become evidence, argument, scope, or conceptual authority. Optional bibliography metadata supplies stable identifiers and verified publication metadata for citations already present in the source; it cannot author a new citation or claim. Peer review is diagnostic and likewise cannot become conceptual authority.

For `journal_academic`, peer review is intentionally open-world and the OpenAI Responses adapter requires hosted web search. External material remains diagnostic evidence only. A discovery is `SOURCE` only when it establishes a material defect in the article's positioning, support, scope, or claims; useful scholarly context that does not make revision necessary may instead be retained as `ADVISORY`.

See `pipeline.md` for the exact stage and failure semantics.

# Build and installation

## Prerequisites

You need GNU Make, Bash, Python >= 3.9, and `curl`. `jq` is optional.

For release-candidate LaTeX validation, install `latexmk`, `biber`, and a LaTeX distribution with BibLaTeX support. Publication additionally uses `pandoc`.

Debian/Ubuntu:

```bash
sudo apt install make python3 curl jq latexmk texlive-latex-extra texlive-bibtex-extra biber pandoc
```

macOS with Homebrew:

```bash
brew install make python curl jq pandoc
```

Install a TeX distribution such as MacTeX separately for PDF validation.

## Configuration

```bash
cp .env.example .env
set -a
source .env
set +a
```

Typical Ollama configuration:

```bash
BACKEND=ollama
OLLAMA_MODEL=llama3.1
OLLAMA_HOST=http://localhost:11434
```

For OpenAI, create a virtual environment and install the provider dependency:

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

ChatGPT subscriptions do not include API usage; API compilation is billed separately.

## Keyless preflight

```bash
make check
```

`make check` performs Python and shell syntax checks, unit/smoke tests, and the repository example's source/bibliography audit. It requires no API key, provider package, running model service, or network access.

The source audit can be run directly:

```bash
make self-preflight
```

Provider connectivity checks are deliberately separate:

```bash
make check-ollama
make openai-check
```

`openai-check` makes a real API request and may incur a charge; it is never part of ordinary CI or `make check`.

## Running the pipeline

The repository example has one end-to-end command:

```bash
make self
```

`make self` runs the keyless source preflight, performs a fresh compilation through the selected backend and target, validates emitted LaTeX stages, audits the final result, and produces `build/final.pdf`. If `BACKEND=openai` is selected, this command makes paid calls.

Generic compilation requires the authoritative source explicitly:

```bash
make final IN=outline.md
```

With verified bibliography metadata:

```bash
make final IN=outline.md BIBLIOGRAPHY=references.bib
```

Individual core stages are:

```bash
make realise IN=outline.md
make review IN=outline.md
make final IN=outline.md
```

`review` depends on `realise`; `final` depends on both and handles the peer-review decision. There are no `draft`, `smooth`, or pre-review `revise` model stages.

An independent summary transform remains available:

```bash
make summarize IN=outline.md
```

This auxiliary transform intrinsically compresses its source and is not part of the core publication graph.

Generated files live under `build/` by default:

- `build/realise.tex`
- `build/peer_review.md`
- `build/final.tex`
- `build/final.pdf` after successful example validation
- `build/references.bib` during example compilation
- `build/openai-usage.jsonl` when OpenAI reports token usage
- `build/summary.tex` when `summarize` is requested
- `build/errors/<stage>.md` for blocking diagnostics

The build root is configurable:

```bash
make BUILD_DIR=/tmp/compiled-prose final IN=outline.md
```

`make validate-latex` validates an already-existing `final.tex` and never triggers model execution. `make clean` removes known generated artefacts from the selected build directory; `make clobber` removes that build directory entirely.

## Peer-review gate

Peer review emits a small machine-readable protocol:

- `PASS` — no material revision is required; the report may still retain nonfatal `ADVISORY` findings, and `realise.tex` is copied exactly to `final.tex` without another model call.
- `REVISE_REALISATION` — at least one `REALISATION` finding and no `SOURCE` finding; exactly one bounded final revision is permitted, while any accompanying advisories remain diagnostic only.
- `BLOCKED_SOURCE` — at least one `SOURCE` finding identifies a defect serious enough to require authorial source work; compilation stops before final revision and emits an external diagnostic.

Malformed or internally inconsistent review status also fails closed. Review suggestions and externally discovered literature never become source authority automatically.

## Release acceptance and publication

Mechanical checks deliberately stop short of claiming semantic equivalence. After a successful self-compilation, a human must compare the candidate final realisation with `outline.md` and the selected target. Confirm that no material claim was introduced without source authority, no represented proposition was strengthened or weakened, no unsupported content-bearing example/theory/citation was added downstream, target-required coverage is appropriate, and qualifications/support relationships remain attached.

Compilation and publication are separate. **Compile self-example target** creates and retains one candidate but cannot deploy Pages. **Publish self-example** is keyless: the operator selects a target, the workflow finds that target's newest successful retained compilation, preserves compatible unselected targets from the latest retained showcase, and deploys through the `github-pages` environment gate. Publishing an existing candidate never invokes the model.

A successful retained candidate contains:

- the authoritative `outline.md`;
- `source-audit.json` and verified `references.bib` provenance metadata;
- `realise.tex`;
- the peer-review report;
- `final.tex` and `final.pdf`;
- compilation commit, model, target, workflow-run metadata, and the human acceptance checklist.

Candidate artifacts are retained for 90 days. The publication assembler compares the authoritative outline bytes before combining target renderings, so an accepted rendering can survive compiler/workflow changes only while the source revision remains identical.

## CI and paid compilation

Ordinary CI is keyless. Pushes and pull requests run `make check` and do not reference provider credentials or make model calls.

Paid example compilation lives only in `.github/workflows/compile-self-example.yml`. It is manual, requires explicit paid-use authorization, is restricted to `main`, and places the provider call behind the `paid-compilation` GitHub Environment. Manual dispatch exposes allowlisted model and target selectors.

A successful compilation normally invokes the selected model twice: once for `realise` and once for peer review. It makes one additional model call only when review returns `REVISE_REALISATION`. `PASS` finalisation is deterministic and `BLOCKED_SOURCE` stops before final revision. The independent `summarize` transform is not invoked by `make final` or `make self`.

Each successful OpenAI response records stage/model/token usage in the transient build usage log. The workflow renders per-stage and total estimated usage into the Actions summary without making another provider call.

Publication lives separately in `.github/workflows/publish-self-example.yml` and is provider-free.

## Reproducibility

Compiled Prose targets semantic and specification-level reproducibility:

- source, prompts, target requirements, stage graph, protocol checks, and configuration are file-driven and inspectable;
- the same authority boundaries and failure rules apply across supported backends;
- a `PASS` review produces an exact deterministic promotion from `realise.tex` to `final.tex`;
- model-generated prose is not promised to be byte-identical across runs, models, provider versions, or platforms.

## Project intent

This repository is both an implementation and its own worked example. Humans author the conceptual source; the realisation stage writes it for a target; peer review supplies the independent second look; another writing pass occurs only when that review identifies a source-and-target-determined realisation defect.
