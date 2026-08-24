# Compilation Pipeline Specification

This document is the canonical specification for the compiled-prose pipeline implemented in this repository. It describes the stage graph, authority model, output/failure protocol, review gate, build-directory behaviour, and reproducibility boundary.

The implementation remains intentionally small: GNU Make orchestrates file dependencies, `tools/render_prompt.py` creates one flattened prompt per model-backed stage, `tools/llm_run.sh` selects the backend, `tools/enforce_protocol.py` enforces the common result protocol, and `tools/review_decision.py` enforces the peer-review decision gate. Provider-specific capabilities remain in their backend adapter; the OpenAI Responses adapter exposes web search only to academic-journal peer review.

Model-backed stage count is part of the user-visible cost surface, not merely an internal architectural choice. Each model-backed stage incurs user-visible execution cost. The existing staged decomposition is retained because empirical use showed that reliable source-to-paper compilation required multiple transformations rather than a one-shot generation. Architectural separation alone is not sufficient justification for adding another model-backed stage: a new stage requires empirical evidence that an existing stage cannot absorb the responsibility reliably without materially degrading compilation quality.

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

The repository self-example adds release-specific mechanical checks around its audited source catalogue and bibliography keys. Those checks verify provenance and rendering integrity for material that is actually emitted; they do not make the generic compiler a semantic citation verifier and do not decide what the selected target should include.

### Prompt contracts

A **prompt contract** is an executable instruction supplied to the model but not semantically proved by the build system. Source fidelity, absence of invented claims, preservation of conceptual scope and conceptual topology, target-relative coverage, rhetorical organisation, summarisation depth, omission choices, faithful attribution/evidence presentation, and correct classification of a review finding as `SOURCE` or `REALISATION` fall into this category.

The build system can detect malformed transport/output structure. It cannot in general prove that valid-looking prose is faithful or target-appropriate. A structurally valid LaTeX result that silently invents a claim, preserves far too much material for a child target, or uses an inappropriate citation presentation is therefore a prompt-contract violation, not something `enforce_protocol.py` can currently discover by itself.

### Design constraints

A **design constraint** states an architectural property future implementation changes are expected to preserve even where no single current test proves it completely. The principal design constraints are backend independence, explicit failure over improvisation, file-driven/Git-friendly operation, keeping conceptual authority upstream of generated prose, model-stage economy, and keeping semantic target decisions in the model/prompt layer rather than duplicating them as deterministic policy code.

Coverage selection, summarisation level, omission, rhetorical organisation, explanatory strategy, and evidence/attribution/citation presentation are semantic target-realisation decisions. Mechanical code may validate protocol and provenance of whatever the model emits, but it must not encode a second deterministic implementation of those target semantics. In particular, deterministic code must not try to force or suppress lists, headings, section counts, or one-source-item mappings as a proxy for prose quality.

Model-stage economy means a conceptual responsibility should be folded into an existing model-backed stage when that stage can perform it reliably. New model-backed stages require empirical justification from compilation quality or failure behaviour; cleaner conceptual decomposition by itself is insufficient because every additional stage increases user cost.

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

Optional bibliography metadata may accompany the source through this graph. It supplies stable identifiers and publication metadata for citations already authored in the source; it does not create another conceptual input and does not by itself require visible formal citation apparatus.

`make summarize` is an independent source-to-LaTeX utility transform. It is not part of the forward `final` dependency chain and may define its own intrinsic coverage reduction as part of that auxiliary stage's responsibility.

## Authority model

Authority is role-specific.

### Authoritative conceptual source

The file supplied as `IN=...` is the authoritative conceptual source for the work. In the repository self-example this is `outline.md`.

Its role is:

- The sole source of conceptual authorship throughout the pipeline.
- The authority for claims, argument, conceptual scope, distinctions, authored examples, evidence, citations, attributions, unresolved authorial choices, and conceptual topology: dependencies, qualification scope, taxonomy membership, semantically meaningful ordering, hierarchy of importance, and support relationships.

Changing a model-generated artefact does not retroactively change this source.

### Stage prompts

`prompts/*.md` define what transformation a stage attempts. They are executable compiler contracts. They may constrain realisation and failure behaviour but are not allowed, by design, to author new conceptual content.

### Target requirements

`prompts/targets/*.md` define audience- or venue-specific realisation requirements: register, reading level, coverage and compression, formatting, evidence/attribution/citation presentation, explanatory explicitness, level of rigour, and similar constraints.

A target is not conceptual authority. In the core publication pipeline, conceptual coverage is exhaustive by default. A target may explicitly authorise summarisation, compression, or selective omission. Those permissions select which source-authorised material appears, and at what resolution, but do not change what the source says or the conceptual scope or meaning of retained material. Omission must not remove qualifications, dependencies, uncertainty, attribution, or context needed to keep retained content faithful and non-misleading. Material omitted from one target realisation remains authoritative source content.

Conceptual topology and presentation topology are deliberately separate. The source is authoritative for substantive relationships among ideas: logical dependencies, qualification and uncertainty scope, taxonomy membership, genuine procedures or ordered sequences, hierarchy of importance, scope, and evidence/attribution/citation attachment. Source bullets, numbering, heading depth, adjacency, fragment boundaries, and navigation order are presentation topology. They may encode a substantive relationship, but they are not target-facing authority merely because the author used them to write the source. Core realisation stages may therefore synthesise, consolidate, split, rhetorically group, and reorder source-authorised material without a special target permission when that changes only presentation topology. A target may further constrain or direct presentation. Semantically meaningful ordering must survive; when changing an ambiguous local order could change meaning, the model is instructed to preserve it or fail closed rather than guess.

Rhetorical reorganisation is not permission to invent connective reasoning. Target-facing grouping must not create a new category, dependency, cause, equivalence, contrast, or warrant, and qualifications, uncertainty, evidence, attribution, and citations must remain attached to the conceptual units they govern.

Evidence, attribution, and citation **presentation** are also target-owned realisation dimensions. The source owns the support relationships and authored citations/attributions; a target may require formal scholarly citation apparatus, ordinary narrative attribution, or explicitly no visible formal citation apparatus. A less formal target is not required to mimic academic citation syntax. It must nevertheless retain whatever attribution or support relationship is necessary for represented material to remain faithful and non-misleading, and it may never invent a source, citation, attribution, or evidentiary relationship.

A target may require greater explicitness, rigour, evidence visibility, attribution, or citation apparatus than the target-independent source-assurance floor, but it may not lower that floor or make an inadequately warranted or materially unsupported source acceptable through a less formal presentation. The source-assurance floor is epistemic rather than stylistic: it does not impose academic prose, scholarly citation apparatus, or academic-style visible argumentation on every target. If satisfying a target requires a claim, item of evidence, citation, attribution, warrant, scope choice, content-bearing example, or other authored material absent from the source, the prompt contract directs the model to fail or report a `SOURCE` defect rather than invent the missing material.

A target may explicitly permit **illustrative scaffolding** as a realisation strategy. Generated examples, analogies, hypotheticals, comparisons, concrete restatements, or similar devices may therefore be absent from the authoritative source without becoming conceptual authorship, provided they only illuminate a source-authorised concept. They may not supply evidence or a missing warrant, introduce a new claim, assumption, scope choice, normative position, or interpretation, resolve an authored ambiguity, or carry argumentative weight that the source does not carry. Their mapping to the source concept must remain traceable and they must be removable without changing what the work claims. Misleading or materially inaccurate scaffolding is a realisation defect; scaffolding that cannot meet those conditions is not permitted.

### Bibliographic rendering metadata

When `BIBLIOGRAPHY=...` is supplied, the referenced bibliography is resolved by `tools/render_prompt.py` and included as a distinct non-conceptual metadata section.

Its role is limited to:

- stable citation identifiers for citations already present in the authoritative source;
- verified bibliographic fields needed when a target uses formal citation rendering;
- a shared provenance/rendering input available to downstream publication tooling.

Bibliographic metadata is **not** authority to introduce a new citation, attribution, claim, content-bearing example, evidence item, theory, or scope choice. A title or other field present only in the bibliography cannot be promoted into essay content merely because the compiler can see it. Supplying bibliography metadata also does not force a target to expose formal citations or a bibliography when that target explicitly requires another presentation.

### Derived stage artefacts

`draft.tex`, `smooth.tex`, and `revise.tex` are working representations. By role they:

- Are inputs to later transformations but are not conceptual authority.
- Must remain faithful to the authoritative source and the selected target's coverage/presentation requirements; content that exists only because an earlier model invented it does not become authoritative by propagation.
- May contain target-permitted illustrative scaffolding without that scaffolding becoming authored content or evidence.

A downstream stage therefore receives the current representation alongside the original source.

### Diagnostic context

`peer_review.md` and files under `$(BUILD_DIR)/errors/` are diagnostics. They can identify problems or request source/realisation work; they do not supply authored answers.

Compilation is deliberately closed-world: draft, smooth, revise, finalisation, and auxiliary prose transforms may use only the authoritative source plus source-supplied bibliography metadata. Academic-journal peer review is the narrow exception. It may inspect external scholarship to challenge novelty and positioning, but any discovered work remains review evidence only. Material that would change the article must be returned upstream as a `SOURCE` finding and can enter later prose only after the author explicitly changes the authoritative source.

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

For a `tex` stage with bibliography metadata, the output contract fixes provenance-safe citation handling rather than imposing one visible citation style. It permits only supplied BibTeX keys and forbids model-authored bibliography entries. If the selected target requires or preserves formal citation apparatus, the prompt instructs the model to use BibLaTeX/biber, the supplied bibliography filename, and no model-authored `thebibliography` block. If the target explicitly requires no formal citation apparatus, the prompt instructs the model not to emit citation commands, bibliography plumbing, or a references section merely because metadata was supplied; necessary source-authored attribution is instead realised in the target-appropriate form. Citation presentation therefore remains target-owned rather than a hidden academic default.

Draft and summarize normally use the authoritative source as their stage input, so the renderer avoids duplicating that payload.

The order above is mechanically fixed by `render_prompt.py`. Conceptual authority is separate from prompt position: the source remains authoritative for content even though system/stage/target instructions constrain execution, coverage, and presentation and bibliography metadata constrains only provenance-safe rendering when used.

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

**Prompt contract:** realise the source faithfully at the selected target's required coverage without inventing claims, relationships, evidence, sources, attributions, citations, content-bearing examples, or authorial choices. Core-pipeline coverage is exhaustive unless the target explicitly authorises reduction. The draft chooses target-facing rhetorical architecture from the source as a whole rather than treating bullets, headings, adjacency, or navigation order as a target-output map. It may synthesise, consolidate, split, group, and reorder presentation while preserving conceptual topology, including genuine procedures, dependencies, taxonomy membership, qualifications, epistemic stance, and support attachment. The model decides which permitted material to compress or omit based on the target contract and source relationships rather than a deterministic selection rule. The target also controls whether source-authorised support appears as formal citations, narrative attribution, or another permitted presentation. When the target explicitly permits illustrative scaffolding, the draft may generate it only under the provenance and fidelity constraints above. Source insufficiency that would require conceptual invention is a blocking condition to report with `@@FAIL`.

### 2. Smooth

**Make target:** `smooth`  
**Stage prompt:** `prompts/20_smooth.md`  
**Inputs:** authoritative source plus `draft.tex` as a derived working artefact, and bibliography metadata when supplied  
**Output:** `$(BUILD_DIR)/smooth.tex`

**Mechanically enforced:** Make orders this after draft and applies the same structural `tex` result protocol.

**Prompt contract:** improve local coherence, readability, integration, and flow without changing the meaning or conceptual relationships of retained content. Inherited stage-input structure is a realisation choice, so smoothing may merge mechanically fragmented units or reduce source-skeleton cadence while preserving genuine ordered/procedural/taxonomic structure and support attachment. The stage must preserve or correct target-authorised coverage and evidence/attribution/citation presentation rather than imposing academic defaults. Earlier drift may be repaired only when the source and target determine the correction; otherwise the stage is instructed to fail closed. Target-permitted illustrative scaffolding may be refined as realisation but never promoted to conceptual authority.

### 3. Revise

**Make target:** `revise`  
**Stage prompt:** `prompts/30_revise.md`  
**Inputs:** authoritative source plus `smooth.tex`, and bibliography metadata when supplied  
**Output:** `$(BUILD_DIR)/revise.tex`

**Mechanically enforced:** Make orders this after smooth and applies the structural `tex` protocol.

**Prompt contract:** tighten the realised prose, document-level coherence, and rhetorical architecture while respecting target-owned coverage and evidence/attribution/citation presentation without expanding conceptual scope or turning target conventions into new content authority. The revision stage judges the realised work by the selected target's normal writing standards and may restructure non-authoritative presentation topology when this improves the work. No particular surface form is intrinsically good or bad; genuine taxonomies, procedures, and other meaningful explicit structures remain valid. Target-permitted illustrative scaffolding remains a removable realisation device rather than authored content.

### 4. Peer review

**Make target:** `review`  
**Stage prompt:** `prompts/40_peer_review.md`  
**Inputs:** authoritative source plus `revise.tex`, target requirements, and bibliography metadata when supplied  
**Output:** `$(BUILD_DIR)/peer_review.md`

**Mechanically enforced at stage publication:** the result uses the declared `md` transport protocol rather than the `tex` protocol.

**Prompt contract:** use this existing review pass for two independent judgements rather than adding another model-backed stage. **Compilation integrity** checks the target-independent source-assurance floor and whether the derived artefact remains a faithful, supportable realisation of the authoritative source under the selected target. **Target writing quality** judges the artefact as writing by the normal standards of the selected target, as though reviewing that kind of work directly rather than auditing a source transformation. Fidelity is not evidence of writing quality: a fully faithful artefact can still require realisation revision because it is weak writing. The reviewer uses ordinary editorial judgement rather than a catalogue of prohibited surface forms, while still respecting the target and the source-authority boundary. Findings remain diagnostic and are classified as source-owned or realisation-owned; review is not permitted to rewrite the source.

For `journal_academic`, normal target quality includes novelty, significance, and scholarly positioning. The reviewer therefore performs a proportional adversarial search for prior formulations, established theories or terminology, adjacent work that narrows the contribution, materially different explanations, and obvious foundational omissions. The purpose is not bibliography growth: only external work that materially changes positioning, support, scope, or the stated contribution should become a finding. A failed search never verifies novelty. Any finding that relies on externally discovered work is `SOURCE`, hence blocking, because the author must decide whether and how to change the authoritative source.

**OpenAI transport configuration:** when the stage is `prompts/40_peer_review.md` and the target is `prompts/targets/journal_academic.md`, `tools/openai_responses.py` supplies the hosted `web_search` tool with required tool use. No prose-producing stage and no other built-in target receives that search capability.

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

Review suggestions never become source authority at this gate. Externally discovered literature follows the same rule, and the academic review contract requires any finding that depends on it to be `SOURCE`, so it cannot flow into the conditional final-realisation path.

### 6. Final realisation revision

**Make target:** reached conditionally through `final`  
**Stage prompt:** `prompts/50_final.md`  
**Precondition:** validated `REVISE_REALISATION` review  
**Inputs:** authoritative source, `revise.tex`, target requirements, validated peer-review diagnostics, and bibliography metadata when supplied  
**Output:** `$(BUILD_DIR)/final.tex`

**Mechanically enforced:** the Makefile exposes only one forward invocation of this model-backed final stage per dependency-chain execution, and its result must satisfy the structural `tex` protocol. There is no automatic route back to peer review.

**Prompt contract:** apply only the validated realisation-level corrections. If a requested correction actually requires authorial source work, the stage is instructed to fail rather than reinterpret diagnostic text as authority. Validated structural findings may be repaired by consolidating, splitting, grouping, or reordering presentation topology while preserving semantically meaningful order, dependency, taxonomy membership, qualification scope, and support attachment; the final stage may not invent connective reasoning to make that restructuring work. Coverage and evidence/attribution/citation presentation remain target-owned; formal citation apparatus may therefore be repaired, transformed, or removed when the target explicitly requires that realisation. Target-permitted illustrative scaffolding may be repaired under the same provenance and fidelity constraints.

## Auxiliary summarize transform

**Make target:** `summarize`  
**Stage prompt:** `prompts/05_summarize.md`  
**Input:** authoritative source (`IN`), plus bibliography metadata when explicitly supplied  
**Output:** `$(BUILD_DIR)/summary.tex`

It uses the same flattened prompt renderer and common stage result protocol but is independent of the core finalisation graph. Its instruction to produce a short summary is an intrinsic stage-level coverage reduction; the core pipeline's default of exhaustive coverage does not override that auxiliary transform.

## Build directory and file lifecycle

`BUILD_DIR ?= build` is the single generated-output root used by the Makefile. Callers may override it, for example:

```bash
make BUILD_DIR=/tmp/compiled-prose final IN=outline.md
```

**Mechanically enforced:** nominal stage artefacts, external diagnostics, and private temporary raw captures are placed under the selected build root. Changing `BUILD_DIR` does not relocate the authoritative source, prompts, target files, or an explicitly supplied source bibliography.

The self-example copies its audited `self-example/references.bib` into the selected build root so any target that uses formal citations can resolve a local `references.bib`. That copy is a disposable build artefact; the source bibliography remains under `self-example/`. Targets that explicitly suppress formal citation apparatus may leave the copied metadata unused in their visible final prose.

`make clean` removes the known pipeline outputs, copied self-example bibliography, and errors directory from the selected build root. `make clobber` removes the selected build root entirely.

Generated artefacts are therefore disposable build products. The source tree remains the authority surface.

## Blocking semantics

The semantic conditions below are **prompt-contract blocking conditions**, not claims of automatic semantic detection. A prose-producing stage is instructed to return `@@FAIL` rather than improvise when faithful output would require it to:

- invent a claim, warrant, content-bearing example, evidence item, source, attribution, or citation;
- use target-permitted illustrative scaffolding as evidence, argument, scope, or conceptual authority;
- choose between unresolved interpretations or contradictory source instructions;
- change authored conceptual scope, conceptual relationships, semantically meaningful order, or claim strength;
- satisfy an additional target-required evidence, explicit-rigour, attribution, or citation obligation not supplied by the source;
- invent connective reasoning or a conceptual relationship in order to make a rhetorical reorganisation coherent;
- repair conceptual drift when the source and target do not uniquely determine the repair.

Target-authorised summarisation, compression, selective omission, target-appropriate reorganisation of non-authoritative presentation topology, or suppression/transformation of formal citation apparatus is not by itself a blocking condition when it remains within the target contract and preserves conceptual topology, meaning, and necessary support relationships of retained material.

Separately, the following are **mechanical blocking conditions** and stop the Make dependency chain:

- backend/prompt-render execution failure;
- empty output;
- malformed or misplaced `@@FAIL` usage;
- violation of the declared `tex`/`md` structural protocol;
- malformed or internally inconsistent peer-review machine status at the final gate;
- a validated `BLOCKED_SOURCE` review;
- explicit `@@FAIL` from the conditional final-realisation stage.

The self-example release path additionally fails closed if its audited bibliography keys do not match `references.bib`, if the final LaTeX invents an unknown citation key, or if formal citation commands that do appear are not correctly bound to the supplied bibliography. It deliberately does **not** fail merely because an authoritative-source citation is absent from the final realisation, nor because a target-facing text does or does not use formal citation apparatus. Whether material should be retained, compressed, omitted, formally cited, or narratively attributed is decided by the model under the selected target and assessed by model review and human acceptance.

Failures are externalised as diagnostics rather than hidden in generated LaTeX.

## Iteration and retry policy

The implemented core is a single forward compilation path: draft -> smooth -> revise -> peer review -> decision -> optional final realisation.

**Mechanically enforced:** there is no review-again edge, recursive Make retry, or automatic source-repair loop in this graph.

**Design constraint:** source-level blockers return control to the human-authored source or explicit compiler configuration. Backend/provider retry policy should not be allowed to mutate source authority or silently reinterpret a semantic failure as success.

**Design constraint:** adding another model-backed stage is not an ordinary refactor. It changes the user's execution cost and therefore requires empirical evidence that the responsibility cannot be handled reliably within the existing bounded stages.

## Backend independence

Backend selection occurs in `tools/llm_run.sh`. Both supported backends consume a rendered prompt on standard input and expose their model result on standard output to the same enforcement layer.

**Design constraint:** backend adapters may handle provider-specific transport and capabilities, but stage prompts, authority semantics, result routing, diagnostics, and review policy remain backend-independent. The OpenAI adapter's academic-review web-search grant is a narrow transport capability, not a new authority channel: all resulting material is still governed by the same `SOURCE`/`REALISATION` review protocol and downstream source boundary.

## Reproducibility boundary

The project targets **semantic and specification-level reproducibility**, not byte-level determinism of model-generated prose.

The stable/reviewable inputs are source files, prompts, target requirements, optional bibliography metadata, Make dependencies, backend/model configuration, and the common enforcement rules. Re-running those inputs should preserve the same authority boundaries, stage responsibilities, conceptual-topology invariants, target-owned coverage/presentation rules, citation identifiers when used, and failure protocol. Target-facing sectioning or sentence-by-sentence structure is intentionally not expected to reproduce source presentation topology deterministically.

Model-generated wording can vary across runs, backends, model revisions, provider implementations, or platforms. Academic peer review with external search also depends on the scholarly web state and search retrieval at run time. Temperature and seed controls may reduce variance where supported; they do not create a repository-wide guarantee of identical bytes or identical search evidence.

One narrow byte-level property is mechanically guaranteed: after a `PASS` review, `final.tex` is an exact copy of `revise.tex` because no final model call occurs.

## File-driven toolchain design

The repository intentionally uses ordinary files and Make dependencies rather than hidden conversational state. Source, prompts, targets, optional bibliography metadata, derived artefacts, and diagnostics can therefore be inspected and diffed with normal development tools.

This is the surviving intent behind the compiler/toolchain framing: predictable stages, explicit authority, explicit failure, stable prompt composition, and disposable generated outputs. It does not require pretending that probabilistic model execution is literally a deterministic compiler backend.