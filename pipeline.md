# Compilation Pipeline Specification

This document is the canonical specification for the compiled-prose pipeline implemented in this repository. It describes the stage graph, authority model, output/failure protocol, review gate, build-directory behaviour, and reproducibility boundary.

The implementation remains intentionally small: GNU Make orchestrates file dependencies, `tools/render_prompt.py` creates one flattened prompt per model-backed stage, `tools/llm_run.sh` selects the backend, `tools/enforce_protocol.py` enforces the common result protocol, and `tools/review_decision.py` enforces the peer-review decision gate.

## Normative vocabulary and enforcement boundary

Not every important property of prose can be checked mechanically. This specification therefore distinguishes three kinds of rule.

### Mechanically enforced rules

A rule labelled **mechanically enforced** is implemented by the Makefile or repository tools/tests. RFC-style words such as **MUST** and **MUST NOT** are reserved here for these rules unless a section explicitly says otherwise.

Mechanical enforcement currently covers matters such as:

- stage ordering through Make dependencies;
- stable prompt composition inputs;
- declared `tex` versus `md` result routing;
- the `@@FAIL` sentinel protocol;
- atomic publication of successful artefacts and external diagnostics;
- removal of stale nominal outputs on failed rebuilds;
- peer-review status syntax and status/finding consistency at the final decision gate;
- deterministic `PASS` promotion from `revise.tex` to `final.tex`;
- the single bounded final-realisation route;
- build-directory isolation for generated artefacts and diagnostics.

The repository self-example adds release-specific mechanical checks around its audited source catalogue and bibliography keys. Those checks do not make the generic compiler a semantic citation verifier.

### Prompt contracts

A **prompt contract** is an executable instruction supplied to the model but not semantically proved by the build system. Source fidelity, absence of invented claims, preservation of scope, and correct classification of a review finding as `SOURCE` or `REALISATION` fall into this category.

The build system can detect malformed transport/output structure. It cannot in general prove that valid-looking prose is faithful. A structurally valid LaTeX result that silently invents a claim is therefore a prompt-contract violation, not something `enforce_protocol.py` can currently discover by itself.

### Design constraints

A **design constraint** states an architectural property future implementation changes are expected to preserve even where no single current test proves it completely. The principal design constraints are backend independence, explicit failure over improvisation, file-driven/Git-friendly operation, and keeping conceptual authority upstream of generated prose.

This distinction is deliberate: the specification does not claim mechanical guarantees that the implementation does not provide.

## Scope

The core compilation path turns one authoritative conceptual source into publication-ready LaTeX through a fixed forward sequence:

```text
authoritative source
      |
      v
    draft
      |
      v
    smooth
      |
      v
    revise
      |
      v
 peer review
      |
      v
review decision
   /       \
 PASS       REVISE_REALISATION
  |                 |
  |                 v
  |          final realisation
  |                 |
  +-----------------+
          |
          v
       final.tex

BLOCKED_SOURCE or malformed review -> external diagnostic + failure
```

Optional bibliography metadata may accompany the source through this graph. It supplies stable identifiers and publication metadata for citations already authored in the source; it does not create another conceptual input.

`make summarize` is an independent source-to-LaTeX utility transform. It is not part of the forward `final` dependency chain.

## Authority model

Authority is role-specific.

### Authoritative conceptual source

The file supplied as `IN=...` is the authoritative conceptual source for the work. In the repository self-example this is `outline.md`.

Its role is:

- The sole source of conceptual authorship throughout the pipeline.
- The authority for claims, argument, structure, scope, distinctions, examples, evidence, citations, and unresolved authorial choices.

Changing a model-generated artefact does not retroactively change this source.

### Stage prompts

`prompts/*.md` define what transformation a stage attempts. They are executable compiler contracts. They may constrain realisation and failure behaviour but are not allowed, by design, to author new conceptual content.

### Target requirements

`prompts/targets/*.md` define audience- or venue-specific realisation requirements: register, reading level, formatting, citation expectations and presentation, and similar constraints.

A target is not conceptual authority. If satisfying it requires a claim, example, item of evidence, citation, or scope choice absent from the source, the prompt contract directs the model to fail rather than invent the missing material.

### Bibliographic rendering metadata

When `BIBLIOGRAPHY=...` is supplied, the referenced bibliography is resolved by `tools/render_prompt.py` and included as a distinct non-conceptual metadata section.

Its role is limited to:

- stable citation identifiers for citations already present in the authoritative source;
- verified bibliographic fields needed by output renderers;
- a shared rendering input that can be consumed independently by LaTeX/BibLaTeX and Pandoc citeproc.

Bibliographic metadata is **not** authority to introduce a new citation, claim, example, evidence item, theory, or scope choice. A title or other field present only in the bibliography cannot be promoted into essay content merely because the compiler can see it.

### Derived stage artefacts

`draft.tex`, `smooth.tex`, and `revise.tex` are working representations. By role they:

- Are inputs to later transformations but are not conceptual authority.
- Must remain faithful to the authoritative source; content that exists only because an earlier model invented it does not become authoritative by propagation.

A downstream stage therefore receives the current representation alongside the original source.

### Diagnostic context

`peer_review.md` and files under `$(BUILD_DIR)/errors/` are diagnostics. They can identify problems or request source/realisation work; they do not supply authored answers.

The model backend is an execution engine, not an authority layer.

## Flattened prompt composition

`tools/render_prompt.py` resolves all file inputs before model execution. Models are never instructed to open repository files themselves.

For each stage the renderer composes one prompt in this stable order:

1. system contract (`prompts/00_system.md`);
2. stage contract;
3. target requirements;
4. authoritative source;
5. bibliographic rendering metadata, only when explicitly supplied;
6. derived stage input, only when it differs from the authoritative source;
7. peer-review diagnostic context, only for the conditional final-realisation stage;
8. declared output and failure contract.

For a `tex` stage with bibliography metadata, the output contract additionally fixes mechanical citation plumbing: exact supplied BibTeX keys, BibLaTeX/biber, the supplied bibliography filename, and no model-authored `thebibliography` block. Citation presentation remains target-owned; parenthetical versus narrative form, author-year versus numeric presentation, and related style choices follow the selected target rather than the protocol. This is a protocol constraint, not conceptual authority.

Draft and summarize normally use the authoritative source as their stage input, so the renderer avoids duplicating that payload.

The order above is mechanically fixed by `render_prompt.py`. Conceptual authority is separate from prompt position: the source remains authoritative for content even though system/stage/target instructions constrain execution and realisation and bibliography metadata constrains citation rendering.

## Stage result protocol

Every model-backed stage declares an output type of `tex` or `md` and produces one raw backend result. The backend output is captured privately before any nominal artefact is published.

### Success

**Mechanically enforced:** a `tex` result MUST be one structurally complete raw LaTeX document: it begins with `\documentclass`, contains an ordered `\begin{document}` / `\end{document}`, and has no non-whitespace content after `\end{document}`.

This is a structural protocol check, not a full TeX compilation or semantic validity proof. The prompt contract additionally asks the model to produce valid LaTeX.

**Mechanically enforced:** an `md` result MUST NOT be a complete LaTeX document according to that structural check. `enforce_protocol.py` does not attempt to implement a general Markdown parser.

For peer review, the stricter line-oriented review grammar is validated later by `review_decision.py` when the final decision is required.

### Explicit stage failure

The prompt contract instructs a stage that cannot faithfully produce its declared artefact to return:

```text
@@FAIL
<Markdown diagnostic>
```

**Mechanically enforced:** `@@FAIL` MUST be the first line with no leading content. The sentinel itself is transport metadata and is stripped before the diagnostic is written to `$(BUILD_DIR)/errors/<stage>.md`.

An empty failure payload is replaced by a protocol-error diagnostic rather than accepted as useful output.

### Execution or protocol failure

**Mechanically enforced:** if prompt rendering/backend execution exits non-zero, or if the raw result violates the declared transport/output protocol:

- the nominal stage output is absent;
- captured partial output is discarded;
- a Markdown diagnostic is atomically written under `$(BUILD_DIR)/errors/`;
- the stage exits non-zero and Make stops the dependency chain.

A subsequent successful rebuild atomically publishes the nominal artefact and removes the stale diagnostic for that stage.

There is no backend-specific enforcement path: OpenAI and Ollama feed the same result boundary.

## Core stages

### 1. Draft

**Make target:** `draft`  
**Stage prompt:** `prompts/10_draft.md`  
**Input:** authoritative source (`IN`), plus bibliography metadata when explicitly supplied  
**Output:** `$(BUILD_DIR)/draft.tex`

**Mechanically enforced:** the source path is required when the draft recipe runs, and a successful result must satisfy the structural `tex` protocol.

**Prompt contract:** expand the source faithfully for the selected target without inventing claims, evidence, citations, examples, or authorial choices. Source insufficiency that would require invention is a blocking condition to report with `@@FAIL`. When bibliography metadata is supplied, use only its exact citation keys for source-authored citations.

### 2. Smooth

**Make target:** `smooth`  
**Stage prompt:** `prompts/20_smooth.md`  
**Inputs:** authoritative source plus `draft.tex` as a derived working artefact, and bibliography metadata when supplied  
**Output:** `$(BUILD_DIR)/smooth.tex`

**Mechanically enforced:** Make orders this after draft and applies the same structural `tex` result protocol.

**Prompt contract:** improve local coherence, readability, and flow without changing conceptual structure or authority. Earlier drift may be repaired only when the source determines the correction; otherwise the stage is instructed to fail closed.

### 3. Revise

**Make target:** `revise`  
**Stage prompt:** `prompts/30_revise.md`  
**Inputs:** authoritative source plus `smooth.tex`, and bibliography metadata when supplied  
**Output:** `$(BUILD_DIR)/revise.tex`

**Mechanically enforced:** Make orders this after smooth and applies the structural `tex` protocol.

**Prompt contract:** tighten the realised prose and global consistency without expanding scope or turning target conventions into new content authority.

### 4. Peer review

**Make target:** `review`  
**Stage prompt:** `prompts/40_peer_review.md`  
**Inputs:** authoritative source plus `revise.tex`, target requirements, and bibliography metadata when supplied  
**Output:** `$(BUILD_DIR)/peer_review.md`

**Mechanically enforced at stage publication:** the result uses the declared `md` transport protocol rather than the `tex` protocol.

**Prompt contract:** inspect the revised artefact against both source and target, localise findings, and classify each finding as source-owned or realisation-owned. Review is diagnostic only and is not permitted to rewrite the source.

The exact machine grammar below is mechanically validated by the final review decision gate. Therefore `make review` alone can publish Markdown that later proves malformed; `make final` will fail closed rather than guess how to interpret it.

### 5. Review decision gate

**Implementation:** `tools/review_decision.py`  
**Inputs:** `peer_review.md`, `revise.tex`  
**Possible result:** deterministic promotion, one final-realisation permission, or failure

The first non-empty review line is exactly one of:

```text
STATUS: PASS
STATUS: REVISE_REALISATION
STATUS: BLOCKED_SOURCE
```

Every later non-empty line has exactly this form:

```text
- [MAJOR|MINOR][SOURCE|REALISATION] <location> :: <finding>
```

**Mechanically enforced:** the report MUST contain exactly one status line, it MUST be the first non-empty line, every finding MUST match the grammar, and the declared status MUST agree with the finding tags:

- any `SOURCE` finding -> `BLOCKED_SOURCE`;
- otherwise one or more findings -> `REVISE_REALISATION`;
- no findings -> `PASS`.

The parser enforces the consistency of the supplied tags. Whether the model classified a finding semantically correctly is a prompt-contract matter.

Decision behaviour is mechanically enforced:

- `PASS` atomically copies the exact contents of `revise.tex` to `final.tex` and makes no model call;
- `REVISE_REALISATION` permits the one conditional final-realisation stage and does not yet create `final.tex`;
- `BLOCKED_SOURCE` removes any stale final output, writes `$(BUILD_DIR)/errors/review.md`, and exits non-zero;
- malformed/inconsistent review likewise writes an external review diagnostic and exits non-zero.

Review suggestions never become source authority at this gate.

### 6. Final realisation revision

**Make target:** reached conditionally through `final`  
**Stage prompt:** `prompts/50_final.md`  
**Precondition:** validated `REVISE_REALISATION` review  
**Inputs:** authoritative source, `revise.tex`, target requirements, validated peer-review diagnostics, and bibliography metadata when supplied  
**Output:** `$(BUILD_DIR)/final.tex`

**Mechanically enforced:** the Makefile exposes only one forward invocation of this model-backed final stage per dependency-chain execution, and its result must satisfy the structural `tex` protocol. There is no automatic route back to peer review.

**Prompt contract:** apply only the validated realisation-level corrections. If a requested correction actually requires authorial source work, the stage is instructed to fail rather than reinterpret diagnostic text as authority.

## Auxiliary summarize transform

**Make target:** `summarize`  
**Stage prompt:** `prompts/05_summarize.md`  
**Input:** authoritative source (`IN`), plus bibliography metadata when explicitly supplied  
**Output:** `$(BUILD_DIR)/summary.tex`

It uses the same flattened prompt renderer and common stage result protocol but is independent of the core finalisation graph.

## Build directory and file lifecycle

`BUILD_DIR ?= build` is the single generated-output root used by the Makefile. Callers may override it, for example:

```bash
make BUILD_DIR=/tmp/compiled-prose final IN=outline.md
```

**Mechanically enforced:** nominal stage artefacts, external diagnostics, and private temporary raw captures are placed under the selected build root. Changing `BUILD_DIR` does not relocate the authoritative source, prompts, target files, or an explicitly supplied source bibliography.

The self-example copies its audited `self-example/references.bib` into the selected build root so the generated LaTeX can resolve a local `references.bib`. That copy is a disposable build artefact; the source bibliography remains under `self-example/`.

`make clean` removes the known pipeline outputs, copied self-example bibliography, and errors directory from the selected build root. `make clobber` removes the selected build root entirely.

Generated artefacts are therefore disposable build products. The source tree remains the authority surface.

## Blocking semantics

The semantic conditions below are **prompt-contract blocking conditions**, not claims of automatic semantic detection. A prose-producing stage is instructed to return `@@FAIL` rather than improvise when faithful output would require it to:

- invent a claim, warrant, example, evidence item, or citation;
- choose between unresolved interpretations or contradictory source instructions;
- change authored scope or claim strength;
- satisfy a target-required evidence/citation obligation not supplied by the source;
- repair conceptual drift when the source does not uniquely determine the repair.

Separately, the following are **mechanical blocking conditions** and stop the Make dependency chain:

- backend/prompt-render execution failure;
- empty output;
- malformed or misplaced `@@FAIL` usage;
- violation of the declared `tex`/`md` structural protocol;
- malformed or internally inconsistent peer-review machine status at the final gate;
- a validated `BLOCKED_SOURCE` review;
- explicit `@@FAIL` from the conditional final-realisation stage.

The self-example release path additionally fails closed if its audited bibliography keys do not match `references.bib`, if the final LaTeX invents an unknown citation key, or if it drops a source-supplied citation. Citation placement and semantic support remain part of human acceptance rather than being falsely claimed as mechanically proved.

Failures are externalised as diagnostics rather than hidden in generated LaTeX.

## Iteration and retry policy

The implemented core is a single forward compilation path: draft -> smooth -> revise -> peer review -> decision -> optional final realisation.

**Mechanically enforced:** there is no review-again edge, recursive Make retry, or automatic source-repair loop in this graph.

**Design constraint:** source-level blockers return control to the human-authored source or explicit compiler configuration. Backend/provider retry policy should not be allowed to mutate source authority or silently reinterpret a semantic failure as success.

## Backend independence

Backend selection occurs in `tools/llm_run.sh`. Both supported backends consume a rendered prompt on standard input and expose their model result on standard output to the same enforcement layer.

**Design constraint:** backend adapters may handle provider-specific transport, but stage prompts, authority semantics, result routing, diagnostics, and review policy remain backend-independent.

## Reproducibility boundary

The project targets **semantic and specification-level reproducibility**, not byte-level determinism of model-generated prose.

The stable/reviewable inputs are source files, prompts, target requirements, optional bibliography metadata, Make dependencies, backend/model configuration, and the common enforcement rules. Re-running those inputs should preserve the same authority boundaries, stage responsibilities, citation identifiers, and failure protocol.

Model-generated wording can vary across runs, backends, model revisions, provider implementations, or platforms. Temperature and seed controls may reduce variance where supported; they do not create a repository-wide guarantee of identical bytes.

One narrow byte-level property is mechanically guaranteed: after a `PASS` review, `final.tex` is an exact copy of `revise.tex` because no final model call occurs.

## File-driven toolchain design

The repository intentionally uses ordinary files and Make dependencies rather than hidden conversational state. Source, prompts, targets, optional bibliography metadata, derived artefacts, and diagnostics can therefore be inspected and diffed with normal development tools.

This is the surviving intent behind the compiler/toolchain framing: predictable stages, explicit authority, explicit failure, stable prompt composition, and disposable generated outputs. It does not require pretending that probabilistic model execution is literally a deterministic compiler backend.
