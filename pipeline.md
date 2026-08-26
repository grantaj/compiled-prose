# Compilation Pipeline Specification

This document is the canonical specification for the compiled-prose pipeline implemented in this repository. It defines the stage graph, authority model, output/failure protocol, peer-review gate, build lifecycle, and reproducibility boundary.

The implementation is intentionally small: GNU Make orchestrates file dependencies, `tools/render_prompt.py` creates one flattened prompt per model-backed stage, `tools/llm_run.sh` selects the backend, `tools/enforce_protocol.py` enforces the common result protocol, and `tools/review_decision.py` enforces the peer-review decision gate. Provider-specific capabilities remain in backend adapters; the OpenAI Responses adapter exposes web search only to academic-journal peer review.

Model-backed stage count is part of the user-visible cost surface. The core pipeline therefore follows a simple rule: **a second writing pass happens only when new information exists that justifies it**. The first model call performs the complete target realisation. Peer review supplies an independent judgement. A final writing call occurs only when review reports a `REALISATION` defect.

This design is motivated by regression evidence, not by a universal claim about every model or source. In the `grantaj/censorship` GPT-5.6 Sol case that prompted the simplification, the former draft-to-smooth pass left about 99.42% of words unchanged and smooth-to-revise left about 99.86% unchanged, at roughly $0.73 combined cost, without repairing the main outline-prosification problem. Peer review was materially more informative. That evidence justifies removing the blind polishing passes while retaining review as an independent stage.

## Normative vocabulary and enforcement boundary

### Mechanically enforced rules

Mechanical enforcement currently covers:

- stage ordering through Make dependencies;
- stable prompt composition inputs;
- declared `tex` versus `md` result routing;
- the `@@FAIL` sentinel protocol;
- atomic publication of successful artefacts and external diagnostics;
- removal of stale nominal outputs on failed rebuilds;
- peer-review status syntax and status/finding consistency;
- deterministic `PASS` promotion from `realise.tex` to `final.tex`;
- exactly one conditional final-revision route;
- build-directory isolation.

The repository example adds release-specific checks around its audited source catalogue and bibliography keys. These verify provenance and rendering integrity for emitted material; they do not implement semantic target selection or prose quality in deterministic code.

### Prompt contracts

Prompt contracts govern properties not mechanically proved by the build system: source fidelity, absence of invented conceptual content, preservation of conceptual topology and epistemic stance, target-relative coverage, rhetorical architecture, writing quality, evidence/attribution/citation presentation, and semantic classification of review findings as `SOURCE` or `REALISATION`.

A structurally valid LaTeX result can still violate these contracts. Mechanical code therefore does not try to force section counts, list usage, source-item mappings, or other surface proxies for prose quality.

### Design constraints

The principal design constraints are backend independence, explicit failure over improvisation, file-driven operation, keeping conceptual authority upstream of generated prose, model-stage economy, and keeping semantic target decisions in the prompt/model layer.

Model-stage economy means a conceptual responsibility should be absorbed into an existing model-backed stage when that stage can perform it reliably. Adding a model call requires empirical justification because it changes the user's cost and latency. Blind smoothing or revision is not justified merely by conceptual neatness.

## Scope and stage graph

The core compilation path is:

```text
authoritative source
      |
      v
   realise
      |
      v
 peer review
      |
      v
review decision
   /       |        \
 PASS   REVISE_      BLOCKED_SOURCE
  |      REALISATION      |
  |          |             `--> diagnostic + failure
  |          v
  |    final revision
  |          |
  +----------+
       |
       v
    final.tex
```

Optional bibliography metadata may accompany the source. It supplies stable identifiers and publication metadata for citations already authored in the source; it is not conceptual input and does not itself require visible formal citation apparatus.

`make summarize` is an independent source-to-LaTeX transform. It is not part of the `final` dependency chain.

## Authority model

### Authoritative conceptual source

The file supplied as `IN=...` is the sole source of conceptual authorship. It defines claims, argument, conceptual scope, distinctions, authored examples, evidence, citations, attributions, unresolved choices, epistemic stance, and conceptual topology: dependencies, qualification scope, taxonomy membership, semantically meaningful ordering, hierarchy of importance, and support relationships.

Changing a generated artefact never changes the source retroactively.

### Stage prompts

`prompts/*.md` define transformations. They constrain realisation, review, and failure behaviour but may not author new conceptual content.

### Target requirements

`prompts/targets/*.md` define audience/venue-specific realisation: register, reading level, coverage and compression, formatting, rhetorical form, explanatory explicitness, evidence/attribution/citation presentation, rigour, and whether illustrative scaffolding is permitted.

Coverage is exhaustive by default. A target may explicitly authorise summarisation, compression, or selective omission, but omission must not make retained content false or misleading or detach necessary qualifications, dependencies, uncertainty, attribution, or support.

Conceptual topology and presentation topology are deliberately separate. Logical dependencies, qualification scope, taxonomy membership, genuine procedures or sequences, hierarchy of importance, scope, and evidence/attribution/citation attachment are authoritative. Bullets, numbering, heading depth, adjacency, fragment boundaries, and navigation order are presentation topology unless they encode one of those substantive relationships. Realisation may synthesize, consolidate, split, rhetorically group, and reorder material without a special target permission when only presentation topology changes. Semantically meaningful ordering must survive.

Rhetorical reorganisation cannot invent connective reasoning, categories, dependencies, causes, equivalences, contrasts, or warrants. Qualifications and support remain attached to the content they govern.

Evidence, attribution, and citation **presentation** is target-owned; evidentiary authority remains source-owned. A target may require formal scholarly citations, ordinary narrative attribution, or no visible formal citation apparatus. It may never invent a source, citation, attribution, or evidentiary relationship.

A target may explicitly permit illustrative scaffolding. Generated analogies, hypotheticals, comparisons, concrete restatements, or similar devices must only illuminate source-authorised concepts. They may not become evidence, a missing warrant, scope, interpretation, or conceptual authority and must be removable without changing the work's claims.

### Bibliographic rendering metadata

When `BIBLIOGRAPHY=...` is supplied, `tools/render_prompt.py` includes it as a distinct non-conceptual metadata section. Its role is limited to stable citation identifiers and verified bibliographic fields for citations already present in the source. It cannot introduce a new citation, attribution, evidence item, theory, claim, or scope choice.

### Derived artefacts

`realise.tex` and, when produced by a conditional repair, `final.tex` are derived representations. They are not conceptual authority. A downstream prose-producing stage receives the current representation alongside the original source so invented or drifted material cannot become authoritative merely through propagation.

### Diagnostic context

`peer_review.md` and `$(BUILD_DIR)/errors/*.md` are diagnostics. They identify defects; they do not supply authored answers.

Compilation is closed-world for prose-producing stages. Academic-journal peer review is the narrow open-world exception: it may inspect external scholarship to challenge novelty, positioning, support, and foundational omissions. External material remains review evidence only. A finding that depends on such material is `SOURCE` and therefore cannot flow into final revision until the author changes the authoritative source.

## Flattened prompt composition

`tools/render_prompt.py` resolves all file inputs before model execution and composes them in this stable order:

1. system contract (`prompts/00_system.md`);
2. stage contract;
3. target requirements;
4. authoritative source;
5. bibliography metadata, when supplied;
6. derived stage input, when it differs from the source;
7. peer-review diagnostic context, for conditional final revision only;
8. output and failure contract.

`realise` and `summarize` normally use the authoritative source as their working input, so the renderer avoids duplicating identical payloads.

For a `tex` stage with bibliography metadata, the output contract permits only supplied bibliography keys. Visible citation presentation remains controlled by the target.

## Stage result protocol

Every model-backed stage declares `tex` or `md` output and produces one raw backend result. Backend output is captured privately before the nominal artefact is published.

### Success

A `tex` result must be one structurally complete raw LaTeX document beginning with `\documentclass`, containing ordered `\begin{document}` / `\end{document}`, and no non-whitespace content after the end marker. This is a transport check, not a semantic proof or full TeX compilation.

An `md` result must not be a complete LaTeX document. Peer review's stricter line-oriented grammar is validated by `review_decision.py` at the final gate.

### Explicit stage failure

A stage that cannot faithfully produce its declared artefact returns:

```text
@@FAIL
<Markdown diagnostic>
```

`@@FAIL` must be the first line. The sentinel is stripped before the diagnostic is written to `$(BUILD_DIR)/errors/<stage>.md`. A failed stage leaves no nominal output.

### Execution or protocol failure

Backend failure, empty output, malformed sentinel use, or transport-protocol failure removes the nominal stage output, writes an external diagnostic, and stops Make. A later successful rebuild atomically replaces the nominal artefact and removes its stale diagnostic.

## Core stages

### 1. Realise

**Make target:** `realise`  
**Stage prompt:** `prompts/10_realise.md`  
**Input:** authoritative source, selected target, and optional bibliography metadata  
**Output:** `$(BUILD_DIR)/realise.tex`

The realisation stage is responsible for the whole writing job in one pass. It must produce target-ready finished writing, not a provisional expansion for later smoothing. It chooses document-level rhetorical architecture from the source as a whole; may synthesise, consolidate, split, subordinate, group, and reorder presentation topology; integrates material into target-appropriate paragraphs or other units; manages transitions, pacing, proportion, and local flow; and uses target-authorised compression without flattening conceptual distinctions.

It must avoid bullet-by-bullet or heading-by-heading prosification while preserving visible structure when that structure itself carries conceptual meaning. Conceptual topology, source authority, epistemic stance, evidence/support attachment, target coverage, and citation-presentation rules remain hard boundaries. Source insufficiency that would require conceptual invention uses `@@FAIL`.

### 2. Peer review

**Make target:** `review`  
**Stage prompt:** `prompts/40_peer_review.md`  
**Inputs:** authoritative source plus `realise.tex`, target requirements, and optional bibliography metadata  
**Output:** `$(BUILD_DIR)/peer_review.md`

Peer review is conceptually independent from realisation. It first judges the realised artefact as though it were submitted directly as finished writing for the selected target. Fidelity, traceability, and visible preservation of source structure are not positive evidence of writing quality. The reviewer then compares identified defects with the source to classify them as `SOURCE` or `REALISATION`, and finally checks compilation integrity for drift and source-assurance failures.

For `journal_academic`, target quality includes novelty, significance, and scholarly positioning. The reviewer performs a proportional adversarial search for prior formulations, established terminology/theories, adjacent work that narrows the contribution, materially different explanations, and foundational omissions. A failed search never verifies novelty. Any material externally discovered finding is `SOURCE` because the author must decide whether and how to change the source.

**OpenAI transport configuration:** when the stage is exactly `prompts/40_peer_review.md` and target exactly `prompts/targets/journal_academic.md`, `tools/openai_responses.py` supplies hosted `web_search` with required tool use. No prose-producing stage or other built-in target receives that capability.

### 3. Review decision gate

**Implementation:** `tools/review_decision.py`  
**Inputs:** `peer_review.md`, `realise.tex`  
**Result:** deterministic promotion, permission for one final revision, or failure

The first non-empty line must be exactly one of:

```text
STATUS: PASS
STATUS: REVISE_REALISATION
STATUS: BLOCKED_SOURCE
```

Every later non-empty line must be:

```text
- [MAJOR|MINOR][SOURCE|REALISATION] <location> :: <finding>
```

Status is mechanically consistent with findings:

- any `SOURCE` finding -> `BLOCKED_SOURCE`;
- otherwise one or more `REALISATION` findings -> `REVISE_REALISATION`;
- no findings -> `PASS`.

Decision behaviour:

- `PASS` atomically copies `realise.tex` to `final.tex` with **no model call**;
- `REVISE_REALISATION` leaves `final.tex` absent and permits exactly one conditional final-revision call;
- `BLOCKED_SOURCE` removes any stale final output, writes `$(BUILD_DIR)/errors/review.md`, and exits non-zero;
- malformed/inconsistent review likewise fails closed with an external diagnostic.

Review text remains diagnostic. It cannot introduce source authority through this gate.

### 4. Conditional final revision

**Make target:** reached only through `final`  
**Stage prompt:** `prompts/50_final.md`  
**Precondition:** validated `REVISE_REALISATION` review  
**Inputs:** authoritative source, `realise.tex`, selected target, validated peer-review findings, and optional bibliography metadata  
**Output:** `$(BUILD_DIR)/final.tex`

This is one bounded writing pass justified by the new information supplied by peer review. It must address validated realisation findings using only corrections fully determined by source and target. Review comments are diagnostic context, not authority. If a requested repair actually requires a new warrant, claim, evidence item, source, citation, conceptual relationship, scope choice, interpretation, or other authorial decision, the stage fails rather than improvising.

There is no automatic route back to peer review and no recursive revision loop.

## Auxiliary summarize transform

**Make target:** `summarize`  
**Stage prompt:** `prompts/05_summarize.md`  
**Input:** authoritative source and optional bibliography metadata  
**Output:** `$(BUILD_DIR)/summary.tex`

This transform is independent of the publication graph and may define intrinsic coverage reduction.

## Build directory and file lifecycle

`BUILD_DIR ?= build` is the generated-output root and may be overridden:

```bash
make BUILD_DIR=/tmp/compiled-prose final IN=outline.md
```

Known core outputs are `realise.tex`, `peer_review.md`, `final.tex`, optional `final.pdf`, and external diagnostics. The self-example also copies its audited bibliography into the build root. `make clean` removes known generated outputs; `make clobber` removes the selected build root entirely.

A successful retained self-example candidate requires `realise.tex`, `peer_review.md`, `final.tex`, and `final.pdf` plus source/provenance files. The publication/showcase assembler consumes final output, review, source, and provenance and does not require removed pre-review intermediate artefacts.

## Blocking semantics

Prompt-contract blocking conditions include any need to invent a claim, warrant, content-bearing example, evidence, source, attribution, citation, conceptual relationship, connective inference, scope decision, or interpretation; choose between unresolved interpretations; change claim strength or meaningful order; satisfy target-required support absent from the source; or repair drift when source and target do not determine the correction.

Mechanical blocking conditions include backend/prompt-render failure, empty output, malformed sentinel use, output-protocol violation, malformed/inconsistent review grammar, validated `BLOCKED_SOURCE`, or `@@FAIL` from conditional final revision.

Failures are externalised rather than embedded in generated LaTeX.

## Iteration and retry policy

The implemented core is a single forward path:

```text
realise -> peer review -> decision -> optional final revision
```

There is no review-again edge, recursive Make retry, automatic source repair, blind smoothing stage, or pre-review revision stage.

Adding another model-backed stage is not an ordinary refactor. It changes user cost and requires empirical evidence that the responsibility cannot be handled reliably within the existing bounded stages.

## Backend independence

Backend selection occurs in `tools/llm_run.sh`. Both supported backends consume rendered prompts on standard input and expose model results to the same enforcement layer. Provider adapters may handle transport-specific capabilities, but authority semantics, prompts, result routing, diagnostics, and review policy remain backend-independent.

The academic-review web-search grant is a narrow provider capability, not an authority channel.

## Reproducibility boundary

The project targets semantic and specification-level reproducibility, not byte-level deterministic prose. Source, prompts, target requirements, optional bibliography metadata, Make dependencies, backend/model configuration, and common enforcement rules are inspectable inputs. Model wording may vary across runs, providers, and model revisions.

One byte-level property is mechanically guaranteed: after a `PASS` review, `final.tex` is an exact copy of `realise.tex` because no final writing call occurs.

## File-driven toolchain design

The repository uses ordinary files and Make dependencies rather than hidden conversational state. Source, prompts, targets, bibliography metadata, derived artefacts, and diagnostics can be inspected and diffed with normal development tools. This is the core of the compiler framing: explicit authority, explicit failure, bounded model calls, stable prompt composition, and disposable generated outputs.
