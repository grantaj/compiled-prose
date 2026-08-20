# Error Handling & Diagnostics in the Compiled-Prose Pipeline

This document specifies how **errors, ambiguities, and blocking issues** are handled in the compiled-prose pipeline. It is intended as **context for a coding agent** implementing or modifying the build system, prompts, or enforcement logic.

The goal is to treat unclear outlines, unsupported claims, or conflicting constraints as **compiler errors**, not as occasions for improvisation.

---

## Design Principles

1. **No silent invention**  
   The language model must never invent content to resolve ambiguity or missing information.

2. **Executable artefacts must remain pure**  
   LaTeX outputs must contain *only* valid LaTeX. Diagnostics must never be embedded in executable artefacts.

3. **Failure is explicit**  
   If a stage cannot be completed correctly, it must fail loudly and early.

4. **Diagnostics are first-class artefacts**  
   Errors are written as structured Markdown files that can be inspected, versioned, and acted upon.

---

## Stage Output Protocol

Each stage follows a strict output protocol depending on its expected artefact type.

### Stages producing LaTeX (`.tex`)

- **On success**:
  - Output *valid LaTeX only*.
  - No commentary, Markdown, or diagnostics.

- **On failure**:
  - Do **not** output LaTeX.
  - Output a diagnostic report beginning with the sentinel line:
    ```
    @@FAIL
    ```
  - Follow with Markdown describing the blocking issues.

### Stages producing Markdown (`.md`, e.g. peer review)

- Output Markdown only.
- No LaTeX.
- May optionally also use `@@FAIL` to signal a hard failure.

---

## Blocking Conditions

A stage **must fail** (emit `@@FAIL`) if any of the following apply:

- The outline lacks sufficient detail to expand a section without inventing claims.
- A claim appears false, unsupported, or dangerously overstated and cannot be repaired without authorial intervention.
- Constraints conflict (e.g. output must be LaTeX only, but commentary is required).
- The input contains contradictions that cannot be resolved without choosing between alternatives.
- Required decisions are missing (definitions, scope boundaries, interpretive stance).

Non-blocking stylistic or editorial issues should *not* trigger failure.

---

## Diagnostic Report Format

When failing, the model should emit a Markdown report of the form:

```markdown
@@FAIL
# Blocking issues

## Missing outline detail
- Section 2.3 asserts X but provides no mechanism or justification.

## Unsupported or risky claims
- Claim: "Academic prose never underwent a conceptual rupture" requires framing or citation guidance.

## Required author decisions
- Clarify whether "gesture" is defined narrowly (rhetorical flourish) or broadly (all stylistic variation).
```

Guidelines:
- Be specific and localised.
- Reference sections, labels, or claims where possible.
- Do not propose fixes that require inventing content.

---

## Enforcement in the Build System

- The build system pipes model output through an enforcement step.
- If output begins with `@@FAIL`:
  - The diagnostic is written to `build/errors/<stage>.md`.
  - The process exits non-zero.
  - `make` halts immediately.

- If no failure sentinel is present:
  - Output is written to the stage’s designated artefact file.

This ensures:
- clean separation of artefacts and diagnostics
- reproducible failure behaviour
- no contamination of LaTeX outputs

---

## Iteration Policy

- The pipeline is defined as a **single forward pass**.
- Failures require **explicit human intervention** (e.g. editing the outline or prompts).
- Automatic retries or self-healing loops are disallowed.

---

## Optional Extensions (Non-Essential)

- **Warnings**: A separate lint or analysis stage may emit non-blocking warnings as Markdown.
- **Checks**: A `make check` target may later enforce simple invariants (e.g. no new sections introduced).

These extensions must not weaken the core failure semantics.

---

## Summary

- Errors are treated as compiler failures, not creative prompts.
- LaTeX outputs remain pure and executable.
- Diagnostics are explicit, structured, and externalised.
- Human authorship remains upstream; the model never guesses.

This error-handling discipline is essential to maintaining conceptual authorship, reproducibility, and trust in the compiled-prose pipeline.