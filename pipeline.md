# Compilation Pipeline Specification

This document defines the **normative semantics** of the compiled‑prose pipeline implemented in this repository. It specifies the required stages, invariants, failure conditions, and artefact boundaries. It is **not** an execution script. Orchestration and scheduling are handled externally by the build system (`make`).

The purpose of this specification is to make the behaviour of the pipeline explicit, inspectable, and auditable, independent of any particular execution environment or language model backend.

---

## Scope

This specification applies to the compilation of a single essay or essay section from an authoritative outline into publication‑ready LaTeX, using a fixed sequence of transformation passes. It governs:

* permitted inputs and outputs
* stage ordering and responsibilities
* file‑modification constraints
* diagnostic and review behaviour
* failure and retry semantics

---

## Authoritative Artefacts

The following artefacts are authoritative by role:

* **Outline** (`outline.md` or section‑level outline):

  * The primary source of conceptual authorship.
  * Defines claims, structure, scope, and invariants.

* **Stage Prompts** (`prompts/*.md`):

  * Define the allowed transformation at each stage.
  * Must not introduce new conceptual content beyond the outline.

* **Target Style Prompt** (`prompts/targets/*.md`):

  * Defines venue‑specific constraints (register, citation style, formatting expectations).

The language model is treated as an **execution engine**, not an author.

---

## Stage Result Protocol

Every stage produces exactly one of two results:

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

For prose-producing stages, source insufficiency is blocking whenever faithful prose would require inventing a claim or warrant, choosing an unresolved interpretation, expanding scope, inventing evidence or citations, changing the strength of an authored claim, or resolving contradictory authoritative input without a defined priority rule. Such conditions must not be hidden in LaTeX comments or repaired downstream.

A diagnostic stage may report defects as its normal Markdown success output; it uses the failure protocol only if the diagnostic stage itself cannot be executed faithfully.

---

## Pipeline Stages (Semantic Order)

The pipeline consists of the following stages, which MUST be applied in order.

### 1. Draft

**Purpose**

* Faithful expansion of the outline into LaTeX prose.

**Inputs**

* Outline
* Draft stage prompt
* System prompt
* Target style prompt

**Output**

* `draft.tex`

**Constraints**

* Output MUST be valid LaTeX.
* No commentary or Markdown on success.
* No claims not grounded in the outline.

---

### 2. Smooth

**Purpose**

* Improve local coherence, readability, and flow without altering structure or claims.

**Input**

* `draft.tex`

**Output**

* `smooth.tex`

**Constraints**

* No new claims or sections.
* Structural order must be preserved.
* Output MUST be valid LaTeX only on success.

---

### 3. Revise

**Purpose**

* Address redundancy, tighten argumentation, and ensure global consistency.

**Input**

* `smooth.tex`

**Output**

* `revise.tex`

**Constraints**

* No expansion of scope.
* Citations, labels, and structure must be preserved unless explicitly corrected.
* Output MUST be valid LaTeX only on success.

---

### 4. Peer Review (Diagnostic)

**Purpose**

* Produce a critical review of the revised LaTeX without modifying it.

**Input**

* `revise.tex`

**Output**

* `peer_review.md`

**Constraints**

* Successful output MUST be Markdown.
* MUST NOT rewrite or paraphrase the text.
* Review should reference sections, labels, or passages in the LaTeX.
* Review content is diagnostic only and has no direct authority.

---

### 5. Final Compilation

**Purpose**

* Reconcile the revised LaTeX with the peer review diagnostics.

**Inputs**

* `revise.tex` (authoritative executable artefact)
* `peer_review.md` (diagnostic context)

**Output**

* `final.tex`

**Constraints**

* Successful output MUST be valid LaTeX only.
* The LaTeX input remains authoritative.
* Peer review comments inform changes but do not override specification.
* No new claims, sections, citations, evidence, or conceptual scope may be introduced.
* A review request that requires authorial source changes is blocking rather than permission for the final stage to invent them.

---

## File‑Modification Rules

* Each stage may publish **only** its designated successful output file or its own external failure diagnostic.
* No stage may modify:

  * the outline
  * prompts
  * target style files
  * successful artefacts from other stages

---

## Determinism and Variance Control

* Given identical inputs, prompts, constraints, backend configuration, and seed (where supported), the pipeline SHOULD produce equivalent outputs.
* Variance is permitted only through explicit configuration changes (e.g. target style, backend, temperature).

---

## Failure Conditions

The pipeline MUST halt and report failure if:

* a prose-producing stage cannot be completed faithfully from authoritative source;
* a stage returns an explicit `@@FAIL` result;
* a backend returns an empty or malformed failure result;
* a backend process fails before a complete result is available;
* a stage violates an enforceable output protocol constraint;
* peer review exposes a blocker that cannot be resolved without authorial source changes.

A failed stage must not leave behind a newly written partial artefact or a stale artefact that appears to be the result of the failed rebuild.

---

## Iteration Policy

* The pipeline is defined as a **single forward pass** through the stages.
* Source-level failures require explicit human intervention in authoritative source or compiler configuration.
* Automatic retries and self-healing for source-level failures are disallowed.
* Any later bounded review/revision semantics must remain explicit rather than becoming an implicit loop.

---

## Status Reporting (Optional)

Execution environments MAY report:

* which files were modified
* a brief summary of changes per stage
* unresolved issues flagged during peer review

Such reporting is diagnostic and does not alter pipeline semantics.

---

## Intent

This specification exists to ensure that the compiled‑prose pipeline is:

* explicit rather than implicit
* inspectable rather than ritualised
* reproducible rather than gestural

It defines *what must be true* of the process, not *how it is run*.
