# Compiled Prose — Project Context for Development Handover

## Purpose of This File
This document provides a **single, high-signal context** for a coding agent (human or AI, e.g. OpenAI Codex in VS Code) taking over development of the *Compiled Prose* toolchain. It explains the **conceptual model**, **current architecture**, **design goals**, and **open questions**, without requiring access to chat history.

This project treats **writing as a compilation pipeline** rather than a single generative act.

---

## 1. Core Concept

**Compiled Prose** models long-form writing (especially academic / theoretical essays) as a deterministic, multi-stage compilation process:

> **Concept & structure = source code**  
> **LLM-generated prose = machine code**  
> **LaTeX = intermediate representation**  
> **PDF = executable artifact**

The key philosophical move is the **separation of concerns**:

- Humans author **ideas, structure, argument, and citations**
- The machine renders **language, flow, and stylistic surface**
- Gesture, expressiveness, and rhetorical flourish are *deliberately removed* from most stages

This is explicitly *not* aimed at poetry or expressive writing, but at:
- academic essays
- theory writing
- technical or conceptual prose
- grant / proposal style texts

---

## 2. Design Principles

### Determinism over creativity
- The pipeline should be *repeatable*
- Same inputs + same prompts → similar outputs
- Creativity is treated as **noise** in most stages

### Multi-stage refinement mirrors human process
The pipeline intentionally mirrors a rigorous human workflow:

1. **Draft** – expand outline into full text
2. **Smooth** – improve flow without adding ideas
3. **Revise** – structural clarity, remove redundancy
4. **Peer Review** – critical feedback (markdown)
5. **Final Revision** – integrate feedback into LaTeX

Each stage has:
- a clearly defined input
- a clearly defined output
- a constrained prompt

---

## 3. File-Based Pipeline Model

Everything is **file-driven** and Git-friendly.

### Author-written (human)
- `prompts/*.md` — stage-specific prompts (the *"compiler flags"*)
- `outline.md` — detailed conceptual outline (this is the *source code*)
- `.env` — environment overrides (API keys, model choice)

### Machine-generated (LLM)
- `build/draft.tex`
- `build/smooth.tex`
- `build/revised.tex`
- `build/peer_review.md`
- `build/final.tex`

Markdown is used for:
- prompts
- peer review

LaTeX is used for:
- all prose-producing stages

---

## 4. Makefile-Driven Orchestration

The pipeline is orchestrated via **GNU Make**, not Python scripts directly.

### Why Make?
- Declarative dependencies
- Partial rebuilds
- Clear execution order
- Familiar to engineers
- Encourages reproducibility

### Typical targets
- `make draft`
- `make smooth`
- `make revise`
- `make peer-review`
- `make final`

Each target:
- reads specific input files
- calls a runner script (Python or shell)
- writes a single output artifact

Make variables define:
- model backend (API vs local)
- temperature / determinism settings
- paths

---

## 5. API vs Local Model Support

The system is explicitly designed to support **multiple LLM backends**:

- OpenAI API (cloud)
- Local models (e.g. Ollama)

### Configuration approach

- `Makefile` defines defaults
- `.env` can override via exported environment variables
- `.env.example` documents required variables

No backend-specific logic should leak into:
- prompts
- outline files
- document structure

Backend selection is **pure configuration**.

---

## 6. Prompt Philosophy

Prompts are treated as **first-class artifacts**.

They are:
- version-controlled
- human-editable
- documented in `pipeline.md`

Prompts act like **stylesheets or compiler passes**, not creative writing instructions.

The same outline should be able to compile into:
- a rigorous academic voice
- a magazine essay
- a simplified explanatory version

…by swapping prompts, not rewriting content.

---

## 7. What This Is *Not*

- Not a chat-based writing tool
- Not an interactive editor
- Not a "just ask the model" system
- Not aimed at fiction or poetry

This is a **batch compiler**, not a conversational partner.

---

## 8. Current State

- Pipeline structure defined
- Makefile logic mostly in place
- Prompt stages exist as `.md`
- LaTeX is the canonical output format
- Peer review stage outputs Markdown
- Final stage merges previous `.tex` with review `.md`

The system already works end-to-end in a basic form.

---

## 9. Open Problems / Future Work

### Technical
- Better error handling and logging
- Determinism controls (seed handling where possible)
- Model-specific quirks isolation
- Improved diff-ability of LaTeX outputs

### Conceptual
- Formalising "style" as reusable prompt modules
- Better metadata flow (citations, notes, TODOs)
- Explicit provenance comments in LaTeX output

### Tooling
- VS Code task integration
- CI support for document builds
- Optional linting of outlines before compilation

---

## 10. Mental Model for the Incoming Coding Agent

Think like:

> **You are building a compiler toolchain, not a chatbot.**

Key priorities:
- clarity of stages
- reproducibility
- explicit inputs/outputs
- minimal magic

If a decision trades off:
- *cleverness* vs *predictability*

Always choose **predictability**.

---

## 11. Guiding Question

> "Could two different agents, human or AI, independently run this pipeline and get functionally equivalent results?"

If yes — the system is working as intended.

---

*End of context file.*