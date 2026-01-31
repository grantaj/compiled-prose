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
* No commentary or Markdown.
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
* Output MUST be valid LaTeX only.

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
* Output MUST be valid LaTeX only.

---

### 4. Peer Review (Diagnostic)

**Purpose**

* Produce a critical review of the revised LaTeX without modifying it.

**Input**

* `revise.tex`

**Output**

* `peer_review.md`

**Constraints**

* Output MUST be Markdown.
* MUST NOT emit LaTeX.
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

* Output MUST be valid LaTeX only.
* The LaTeX input remains authoritative.
* Peer review comments inform changes but do not override specification.
* No new claims, sections, or conceptual scope may be introduced.

---

## File‑Modification Rules

* Each stage may modify **only** its designated output file.
* No stage may modify:

  * the outline
  * prompts
  * target style files
  * artefacts from other stages

---

## Determinism and Variance Control

* Given identical inputs, prompts, constraints, backend configuration, and seed (where supported), the pipeline SHOULD produce equivalent outputs.
* Variance is permitted only through explicit configuration changes (e.g. target style, backend, temperature).

---

## Failure Conditions

The pipeline MUST halt and report failure if:

* a stage cannot be completed due to insufficient outline detail
* a stage violates its output format constraints
* a peer review reports blocking issues that cannot be resolved without expanding scope

Failures should be reported explicitly rather than worked around implicitly.

---

## Iteration Policy

* The pipeline is defined as a **single forward pass** through the stages.
* Any iteration (e.g. re‑review after final compilation) MUST be explicit and bounded by the execution environment.
* Unbounded or implicit loops are disallowed.

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
