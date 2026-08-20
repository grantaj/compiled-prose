# Compilation Pipeline Specification

This document defines the **normative semantics** of the compiled-prose pipeline implemented in this repository. It specifies the required stages, invariants, failure conditions, and artefact boundaries. It is **not** an execution script. Orchestration and scheduling are handled externally by the build system (`make`).

The purpose of this specification is to make the behaviour of the pipeline explicit, inspectable, and auditable, independent of any particular execution environment or language model backend.

---

## Scope

This specification applies to the compilation of a single essay or essay section from an authoritative outline into publication-ready LaTeX, using a fixed sequence of transformation passes. It governs:

* permitted inputs and outputs
* stage ordering and responsibilities
* target-specific rendering constraints
* file-modification constraints
* diagnostic and review behaviour
* failure and retry semantics

---

## Authoritative Artefacts

The following artefacts are authoritative by role:

* **Authoritative source** (`outline.md` or other explicitly authored source material):

  * The sole source of conceptual authorship throughout the pipeline.
  * Defines claims, argument, structure, scope, distinctions, examples, evidence, citations, and unresolved authorial choices.

* **Stage Artefacts** (`draft.tex`, `smooth.tex`, `revise.tex`):

  * Derived working representations produced by compiler stages.
  * Are inputs to later transformations but are not conceptual authority.
  * Must remain faithful to the authoritative source; a claim, citation, example, or scope change appearing only in a stage artefact does not become authored content merely by surviving to a later stage.

* **Stage Prompts** (`prompts/*.md`):

  * Define the transformation performed at each stage.
  * May constrain realisation but must not introduce new conceptual content.

* **Target Requirements** (`prompts/targets/*.md`):

  * Define venue- or audience-specific realisation constraints such as register, reading level, formatting, citation expectations, and audience assumptions.
  * Must not introduce claims, arguments, examples, evidence, citations, or conceptual scope.

* **Diagnostic Context** (for example `peer_review.md`):

  * Identifies defects or requested realisation-level changes.
  * Is advisory and has no authority to change the argument or supply missing authored content.

The language model is treated as an **execution engine**, not an author.

---

## Prompt Authority and Content Authority

The authority relationship remains stable:

1. system instructions;
2. stage prompt;
3. target requirements;
4. authoritative source;
5. diagnostic context, when present.

The prompt renderer composes system, stage, target, and authoritative source in that order. When the current stage input differs from the authoritative source, it is then included as a separately labelled **derived working artefact** before diagnostic context. The stage input is not an additional authority layer. The explicit output contract is protocol-level system instruction and cannot be overridden by any prompt content.

Instruction precedence is not conceptual authorship. The authoritative source remains the sole authority for what the work says. Higher-priority system, stage, and target instructions may define compiler behaviour or acceptable realisation, but they may not license new conceptual content. A downstream stage must not promote an invention or omission in a derived stage artefact into authored content.

In particular:

* a stage prompt defines **what transformation is being performed**;
* a target defines **what constitutes acceptable realisation for the selected audience or venue**;
* the authoritative source defines **what the work says**;
* a stage artefact is the current working representation to transform and must be checked against that source;
* diagnostic context may identify defects but cannot supply the missing answer.

If satisfying a target requirement would require evidence, a citation, an example, a new claim, a scope decision, or another authored choice absent from the authoritative source, the relevant prose-producing stage must fail closed rather than inventing it. A diagnostic stage should report such a defect as its normal diagnostic output.

The build system carries the original authoritative source alongside each downstream stage artefact. Draft and summarise operate directly on that source; smooth, revise, review, and the optional final realisation revision receive both the original source and the derived artefact they are transforming or inspecting.

---

## Stage Result Protocol

Every model-backed stage produces exactly one of two results:

1. **Success** — a complete artefact of the stage's declared output type (`tex` or `md`).
2. **Failure** — a Markdown diagnostic beginning in the raw backend response with the sentinel line `@@FAIL`.

The sentinel is a transport protocol marker, not part of the diagnostic artefact. The build system removes it and writes the remaining Markdown to `$(BUILD_DIR)/errors/<stage>.md`.

The backend output is never written directly to the nominal stage artefact. It is captured privately and passed through one backend-independent protocol enforcement boundary. A successful result is published only after that check succeeds. The declared success type is enforced at this boundary: current `tex` stages must return one structurally complete raw LaTeX document (`\documentclass` through `\end{document}` with no trailing content), while an `md` stage must not return a complete LaTeX document. This structural check does not replace later LaTeX compilation or semantic validation.

On failure:

* the nominal stage artefact is absent, including any stale result from a previous successful build;
* the external diagnostic is written under the configured build directory;
* any diagnostic from a previous attempt at that stage is replaced rather than left deceptively current;
* the stage exits non-zero and `make` stops;
* no automatic retry or source-level self-healing is attempted.

If prompt rendering or backend execution exits non-zero before a complete model result exists, the captured partial output is discarded and the same external diagnostic path records an execution failure. Such an infrastructure failure is not misreported as an authorial source defect.

On a later success, the nominal artefact is published and any stale diagnostic for that stage is removed.

For prose-producing stages, source insufficiency is blocking whenever faithful prose would require inventing a claim or warrant, choosing an unresolved interpretation, expanding scope, inventing evidence or citations, satisfying a target-required evidence or citation obligation that the authoritative source does not supply, changing the strength of an authored claim, or resolving a contradiction in the authoritative source without a defined priority rule. Such conditions must not be hidden in LaTeX comments or repaired downstream.

A diagnostic stage may report defects as its normal Markdown success output; it uses the failure protocol only if the diagnostic stage itself cannot be executed faithfully.

---

## Peer-review Decision Protocol

Peer review has an additional machine-readable protocol because a successful diagnostic can still determine whether compilation is allowed to continue.

The first non-empty line of `peer_review.md` is exactly one of:

* `STATUS: PASS`
* `STATUS: REVISE_REALISATION`
* `STATUS: BLOCKED_SOURCE`

Every subsequent non-empty line is one localised finding of the form:

`- [MAJOR|MINOR][SOURCE|REALISATION] <location> :: <finding>`

The overall status is not discretionary metadata. It is mechanically implied by the findings:

* any `SOURCE` finding implies `BLOCKED_SOURCE`;
* otherwise one or more `REALISATION` findings imply `REVISE_REALISATION`;
* no findings imply `PASS`.

The build system validates both the syntax and this consistency rule. A missing, duplicated, unknown, malformed, or inconsistent status fails closed rather than being guessed or repaired.

`SOURCE` means that satisfying the finding requires authorial source work: for example a missing warrant, unsupported non-trivial claim, missing required evidence or citation, contradiction, meaning-changing ambiguity, missing scope boundary, or material expansion. `REALISATION` means that the existing source completely determines the correction and only wording or presentation changes.

If classification is ambiguous, the finding is source-level. A reviewer-suggested citation or evidence item absent from the authoritative source never becomes authority by appearing in the review.

The decision gate acts as follows:

* `PASS`: `revise.tex` is promoted deterministically to `final.tex`; no final model revision is run.
* `REVISE_REALISATION`: exactly one named final realisation-revision stage may run.
* `BLOCKED_SOURCE`: compilation stops non-zero before final revision, any nominal `final.tex` is removed, and the review is surfaced under the normal external diagnostic path for human source revision.

There is no review-again flag and no route from this protocol back into peer review automatically.

---

## Pipeline Stages (Semantic Order)

The pipeline consists of the following stages and decision gate, applied in order.

### 1. Draft

**Purpose**

* Faithful expansion of the outline into LaTeX prose realised for the selected target.

**Inputs**

* Outline
* Draft stage prompt
* System prompt
* Target requirements

**Output**

* `draft.tex`

**Constraints**

* Output MUST be valid LaTeX.
* No commentary or Markdown on success.
* No claims not grounded in the outline.
* Target-required citations may only come from the authoritative source; missing required support is blocking.

---

### 2. Smooth

**Purpose**

* Improve local coherence, readability, and flow without altering structure or claims, while preserving the selected target requirements.

**Inputs**

* authoritative source
* `draft.tex` (derived stage input)

**Output**

* `smooth.tex`

**Constraints**

* No new claims or sections.
* Structural order must be preserved.
* Drift between `draft.tex` and the authoritative source may be repaired only when the correction is fully determined by the source; otherwise the stage must fail closed.
* Citation handling is conditional on supplied citations and target requirements.
* Output MUST be valid LaTeX only on success.

---

### 3. Revise

**Purpose**

* Address redundancy, tighten prose realisation, and ensure global consistency for the selected target.

**Inputs**

* authoritative source
* `smooth.tex` (derived stage input)

**Output**

* `revise.tex`

**Constraints**

* No expansion of scope.
* Drift between `smooth.tex` and the authoritative source may be repaired only when the correction is fully determined by the source; otherwise the stage must fail closed.
* Citations, labels, and structure must be preserved unless a permitted realisation-level correction is made.
* No academic or other venue-specific norm may be imposed unless it comes from the selected target.
* Output MUST be valid LaTeX only on success.

---

### 4. Peer Review (Diagnostic)

**Purpose**

* Produce a critical, classified review of the revised LaTeX against the selected target without modifying it.

**Inputs**

* authoritative source
* `revise.tex` (derived stage input)
* Target requirements

**Output**

* `peer_review.md`

**Constraints**

* Successful output MUST be Markdown conforming to the peer-review decision protocol above.
* MUST NOT rewrite or paraphrase the text.
* Every finding must be localised and classified by severity and by `SOURCE` versus `REALISATION` ownership.
* Review must identify material drift between the derived stage input and the authoritative source; such drift does not become authoritative by propagation.
* Tone, structure, reading level, formatting, citation expectations, and related criteria must be assessed against the selected target rather than an assumed academic venue.
* Scholarly citation checks apply when the selected target requires them; a non-academic target must not inherit academic reference obligations.
* Missing target-required evidence or citations are source defects to report, not material for the reviewer to invent.
* Review content is diagnostic only and has no direct authority.

---

### 5. Review Decision Gate

**Purpose**

* Validate review syntax and authority classification and choose the only permitted next action.

**Inputs**

* `peer_review.md`
* `revise.tex`

**Outputs**

* on `PASS`, `final.tex` as an exact deterministic promotion of `revise.tex`;
* on `REVISE_REALISATION`, permission for stage 6 and no nominal `final.tex` yet;
* on `BLOCKED_SOURCE` or malformed review, a non-zero exit and external diagnostic with no nominal `final.tex`.

**Constraints**

* The gate is deterministic and makes no model call.
* It never converts review suggestions into source authority.
* It fails closed on malformed or inconsistent review status.

---

### 6. Final Realisation Revision (Conditional, Bounded)

**Purpose**

* Apply the validated realisation-only peer-review findings once.

**Precondition**

* The review decision gate returned `REVISE_REALISATION`.

**Inputs**

* authoritative source
* `revise.tex` (derived stage input)
* target requirements
* validated `peer_review.md` (diagnostic context containing only `REALISATION` findings)

**Output**

* `final.tex`

**Constraints**

* This stage may execute at most once per forward compilation.
* Successful output MUST be valid LaTeX only.
* The authoritative source remains authoritative for conceptual content; the LaTeX stage input is only a derived working artefact.
* Target requirements control acceptable realisation but do not author content.
* Peer review comments inform changes but do not override specification or source authority.
* No new claims, sections, citations, evidence, examples, or conceptual scope may be introduced.
* If a supposedly realisation-level finding turns out to require authorial source changes, the stage must fail closed rather than reinterpret the review as authority.
* The stage cannot request or trigger another review pass.

---

## File-Modification Rules

* Each stage may publish **only** its designated successful output file or its own external failure diagnostic.
* The deterministic review decision gate may promote `revise.tex` to `final.tex` on `PASS`, or remove a stale `final.tex` when compilation is blocked.
* No stage may modify:

  * the outline
  * prompts
  * target requirement files
  * successful artefacts from other stages

---

## Determinism and Variance Control

* Given identical inputs, prompts, constraints, backend configuration, and seed (where supported), the pipeline SHOULD produce equivalent outputs.
* Variance is permitted only through explicit configuration changes (e.g. target, backend, temperature).
* A `PASS` review introduces no additional model variance because finalisation is deterministic promotion.

---

## Failure Conditions

The pipeline MUST halt and report failure if:

* a prose-producing stage cannot be completed faithfully from the authoritative source;
* a target requirement cannot be met without inventing authored content, evidence, or citations;
* a stage returns an explicit `@@FAIL` result;
* a backend returns an empty or malformed failure result;
* a backend process fails before a complete result is available;
* a stage violates an enforceable output protocol constraint;
* peer review returns a malformed or internally inconsistent machine status;
* peer review exposes a source-level blocker that cannot be resolved without authorial source changes;
* the bounded final realisation revision discovers that a requested correction actually requires authorial source work.

A failed stage or decision gate must not leave behind a newly written partial artefact or a stale artefact that appears to be the result of the failed rebuild.

---

## Iteration Policy

* The pipeline is a **single forward pass**: draft -> smooth -> revise -> peer review -> decision gate -> optional one-time final realisation revision.
* Source-level failures require explicit human intervention in authoritative source or compiler configuration.
* Automatic retries and self-healing for source-level failures are disallowed.
* `REVISE_REALISATION` permits at most one final realisation-revision pass and never another peer-review pass.
* `PASS` performs no model-backed revision after peer review.
* There is no hidden retry loop, recursive make invocation, or reviewer-driven self-improvement cycle.

---

## Status Reporting (Optional)

Execution environments MAY report:

* which files were modified
* a brief summary of changes per stage
* unresolved issues flagged during peer review

Such reporting is diagnostic and does not alter pipeline semantics.

---

## Intent

This specification exists to ensure that the compiled-prose pipeline is:

* explicit rather than implicit
* inspectable rather than ritualised
* reproducible rather than gestural

It defines *what must be true* of the process, not *how it is run*.
