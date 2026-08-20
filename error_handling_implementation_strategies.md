# Implementation Strategies for Error Handling and Pipeline Enforcement

This document summarises the **recommended concrete implementation strategies** for enforcing error handling, diagnostics, and stage discipline in the compiled-prose pipeline. It is intended as **handover context for a coding agent** responsible for implementing or refining the build system.

This document complements:
- `PIPELINE_SPEC.md` (normative semantics)
- `ERROR_HANDLING.md` (failure protocol and diagnostics)

It focuses on *how* those rules are realised in code.

---

## Overall Architecture

The pipeline is implemented as a classic Unix-style stream:

```
(render_prompt) → (LLM backend) → (protocol enforcement) → (artefact or error)
```

Key principle:

> **The language model never decides whether it succeeded; the build system does.**

---

## Prompt Composition (Flattening)

### Strategy

- Prompts must be **fully resolved before execution**.
- The LLM must receive a *single, flattened prompt* per stage.
- No prompt should instruct the model to "read" other files.

### Implementation

- Use a small script (e.g. `render_prompt.py`) to concatenate:
  - system prompt
  - target style prompt
  - stage prompt
  - primary input (outline or LaTeX)
  - optional diagnostic context (peer review)

The order must be stable and explicit.

---

## Stage Output Protocol Enforcement

### Strategy

- Each stage declares an **expected output type** (`tex` or `md`).
- The model emits either:
  - a valid artefact of that type, or
  - a failure sentinel followed by diagnostics.

### Failure Sentinel

- Use a fixed, unambiguous marker:
  ```
  @@FAIL
  ```

- The marker must appear at the start of output.

---

## Enforcement Wrapper Script

### Strategy

Introduce a small wrapper (e.g. `enforce_protocol.py`) that:

1. Reads model output from `stdin`.
2. Checks for the failure sentinel.
3. Routes output accordingly.

### Behaviour

- If output starts with `@@FAIL`:
  - Write the full output to `build/errors/<stage>.md`.
  - Exit with non-zero status.
  - Cause `make` to halt.

- Otherwise:
  - Write output verbatim to the designated artefact file.

This wrapper is the **single enforcement point** for correctness.

---

## Makefile Integration

### Strategy

- All stage rules pipe model output into the enforcement wrapper.
- The Makefile never writes model output directly to files.

### Example Pattern

```make
$(DRAFT_OUT): ...
	$(call RUN_LLM,...) \
	| python tools/enforce_protocol.py \
	    --stage draft \
	    --expected tex \
	    --out "$@"
```

This ensures that:
- malformed output never reaches artefacts
- failures propagate naturally via exit codes

---

## Error Artefact Management

### Strategy

- All diagnostics are written to a dedicated directory:
  ```
  build/errors/
  ```

- Filenames correspond to pipeline stages:
  ```
  draft.md
  revise.md
  final.md
  ```

This keeps errors inspectable and versionable without polluting outputs.

---

## Backend Independence

### Strategy

- Backend selection (`ollama` vs `openai`) occurs **outside** enforcement logic.
- All backends must:
  - read from `stdin`
  - write to `stdout`
  - propagate failure only via content (sentinel) or exit code

### Implementation

- Use a dispatcher script (e.g. `llm_run.sh`) that selects the backend.
- Enforcement logic must be backend-agnostic.

---

## Determinism Controls

### Strategy

- Determinism is controlled by configuration, not code branching.
- Relevant parameters:
  - model name
  - temperature
  - seed (where supported)

### Implementation

- Pass configuration exclusively via environment variables.
- Record configuration externally if reproducibility tracking is needed.

---

## Failure Propagation Semantics

### Strategy

- Any stage failure stops the pipeline immediately.
- No retries or fallback behaviour inside the build system.

### Rationale

- Forces ambiguity and conceptual gaps back to the outline.
- Prevents silent degradation of conceptual authorship.

---

## Optional Extensions (Strictly Optional)

These may be implemented later but are not required:

- `make check` target for lightweight invariant checks
- separate lint / warning stage (non-blocking Markdown output)
- manifest file recording inputs, hashes, and configuration

None of these should weaken the core enforcement model.

---

## Summary for Coding Agent

- Flatten prompts before execution.
- Treat the LLM as a pure transform.
- Enforce success/failure outside the model.
- Keep LaTeX outputs uncontaminated.
- Write diagnostics as explicit artefacts.
- Let `make` handle ordering and halting.

These strategies operationalise the compiled-prose model as real infrastructure, not prompting convention.

