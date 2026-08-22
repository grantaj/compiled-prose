SHELL := /usr/bin/env bash
.SHELLFLAGS := -euo pipefail -c

# Load .env outside of Make (e.g., export vars in your shell) if needed.

BUILD_DIR ?= build

# Backend selection (can be overridden: make BACKEND=openai final)
BACKEND ?= ollama
LLM_RUNNER ?= bash tools/llm_run.sh

# OpenAI config
OPENAI_MODEL ?= gpt-5
OPENAI_TEMPERATURE ?= 0.2
OPENAI_SEED ?= 42
OPENAI_USAGE_LOG ?= $(BUILD_DIR)/openai-usage.jsonl

# Ollama config
OLLAMA_MODEL ?= llama3.1
OLLAMA_HOST ?= http://localhost:11434

# Release/self-example builds can opt into transport validation after every
# emitted LaTeX stage. Generic compilation remains independent of a TeX install.
VALIDATE_LATEX_STAGES ?= 0

# Inputs
IN ?=
BIBLIOGRAPHY ?=
SYSTEM := prompts/00_system.md
CITATION_PROTOCOL := prompts/citation_protocol.md
TARGET_STYLE ?= prompts/targets/journal_academic.md
SELF_SOURCE := outline.md
SELF_SOURCE_AUDIT := self-example/source-audit.json
SELF_BIBLIOGRAPHY := self-example/references.bib
BUILD_BIBLIOGRAPHY := $(BUILD_DIR)/references.bib

P_DRAFT := prompts/10_draft.md
P_SMOOTH := prompts/20_smooth.md
P_REVISE := prompts/30_revise.md
P_REVIEW := prompts/40_peer_review.md
P_FINAL := prompts/50_final.md

# Outputs
DRAFT_OUT   := $(BUILD_DIR)/draft.tex
SMOOTH_OUT  := $(BUILD_DIR)/smooth.tex
REVISE_OUT  := $(BUILD_DIR)/revise.tex
REVIEW_OUT  := $(BUILD_DIR)/peer_review.md
FINAL_OUT   := $(BUILD_DIR)/final.tex
FINAL_PDF   := $(BUILD_DIR)/final.pdf
SUMMARY_OUT := $(BUILD_DIR)/summary.tex
ERROR_DIR   := $(BUILD_DIR)/errors

.PHONY: all draft smooth revise review final summarize self self-preflight validate-latex check check-python check-shell test check-ollama openai-check print-vars clean clobber
all: final
draft: $(DRAFT_OUT)
smooth: $(SMOOTH_OUT)
revise: $(REVISE_OUT)
review: $(REVIEW_OUT)
final: $(FINAL_OUT)
summarize: $(SUMMARY_OUT)

# Provider-free release-readiness checks for the repository's authoritative
# self-example source and its non-conceptual bibliography metadata.
self-preflight:
	@python tools/audit_self_example.py --outline "$(SELF_SOURCE)" --audit "$(SELF_SOURCE_AUDIT)" --bibliography "$(SELF_BIBLIOGRAPHY)"

# One obvious end-to-end self-example command. This deliberately performs a
# fresh build. The selected BACKEND controls whether model execution is local
# or paid; self-preflight always runs before any backend invocation. Release
# validation checks each emitted LaTeX stage before another model stage runs.
self: self-preflight
	@$(MAKE) --no-print-directory clobber
	@mkdir -p "$(BUILD_DIR)"
	@cp "$(SELF_BIBLIOGRAPHY)" "$(BUILD_BIBLIOGRAPHY)"
	@$(MAKE) --no-print-directory IN="$(SELF_SOURCE)" BIBLIOGRAPHY="$(BUILD_BIBLIOGRAPHY)" VALIDATE_LATEX_STAGES=1 final
	@python tools/audit_self_example.py --outline "$(SELF_SOURCE)" --audit "$(SELF_SOURCE_AUDIT)" --bibliography "$(BUILD_BIBLIOGRAPHY)" --final "$(FINAL_OUT)"
	@$(MAKE) --no-print-directory validate-latex

# Validation is intentionally non-compiling at the prose-pipeline level: if
# final.tex does not already exist, fail rather than triggering a model stage.
validate-latex:
	@if [ ! -f "$(FINAL_OUT)" ]; then echo "$(FINAL_OUT) does not exist; compile it before LaTeX validation" >&2; exit 2; fi
	@python tools/validate_latex.py --input "$(FINAL_OUT)" --output "$(FINAL_PDF)"

# Fast local preflight. These dependencies must remain keyless and provider-free.
check: check-python check-shell test self-preflight

check-python:
	@python -m py_compile tools/*.py tests/*.py

check-shell:
	@for script in tools/*.sh; do bash -n "$$script"; done

test:
	@python -m unittest discover -s tests -v

check-ollama:
	@python tools/check_ollama.py

openai-check:
	@printf 'ping' | BACKEND=openai OPENAI_MODEL=$(OPENAI_MODEL) \
	  python tools/openai_responses.py >/dev/null && \
	echo "OpenAI OK" || \
	( echo "OpenAI request failed; check API key and billing." >&2; exit 1 )

print-vars:
	@echo "IN=$(IN)"
	@echo "BIBLIOGRAPHY=$(BIBLIOGRAPHY)"
	@echo "OPENAI_USAGE_LOG=$(OPENAI_USAGE_LOG)"
	@echo "MAKEFLAGS=$(MAKEFLAGS)"


$(BUILD_DIR):
	mkdir -p "$(BUILD_DIR)"

define RUN_LLM
python tools/render_prompt.py \
  --system $(SYSTEM) --stage $(1) --target $(TARGET_STYLE) --source $(IN) --in $(2) --output-type $(3) \
  --citation-protocol $(CITATION_PROTOCOL) \
  $(if $(strip $(BIBLIOGRAPHY)),--bibliography $(BIBLIOGRAPHY),) $(4) \
| BACKEND=$(BACKEND) \
  OPENAI_MODEL=$(OPENAI_MODEL) OPENAI_TEMPERATURE=$(OPENAI_TEMPERATURE) OPENAI_SEED=$(OPENAI_SEED) \
  COMPILED_PROSE_STAGE=$(1) OPENAI_USAGE_LOG="$(OPENAI_USAGE_LOG)" \
  OLLAMA_MODEL=$(OLLAMA_MODEL) OLLAMA_HOST=$(OLLAMA_HOST) \
  $(LLM_RUNNER)
endef

# Capture backend output privately, then publish the nominal artefact only after
# the backend-independent success/failure protocol has been enforced. Release
# builds additionally compile every emitted TeX artefact before proceeding, but
# do not rewrite or repair model output mechanically.
define RUN_STAGE
rm -f "$(5)" "$(ERROR_DIR)/$(1).md"; \
raw="$$(mktemp "$(BUILD_DIR)/.$(1).raw.XXXXXX")"; \
trap 'rm -f "$$raw"' EXIT; \
if $(call RUN_LLM,$(2),$(3),$(4),$(6)) > "$$raw"; then \
  python tools/enforce_protocol.py \
    --stage "$(1)" --output-type "$(4)" \
    --output "$(5)" --diagnostic "$(ERROR_DIR)/$(1).md" < "$$raw"; \
  if [ "$(VALIDATE_LATEX_STAGES)" = "1" ] && [ "$(4)" = "tex" ]; then \
    validation_dir="$(ERROR_DIR)/latex-$(1)"; \
    rm -rf "$$validation_dir"; \
    python tools/validate_latex.py \
      --input "$(5)" --output "$$validation_dir/validated.pdf" \
      --diagnostic-dir "$$validation_dir"; \
    rm -rf "$$validation_dir"; \
  fi; \
else \
  status="$$?"; \
  python tools/enforce_protocol.py \
    --stage "$(1)" --output-type "$(4)" \
    --output "$(5)" --diagnostic "$(ERROR_DIR)/$(1).md" \
    --backend-exit-status "$$status" < "$$raw" || protocol_status="$$?"; \
  exit "$${protocol_status:-2}"; \
fi
endef

DRAFT_IN := $(IN)

$(DRAFT_OUT): $(BUILD_DIR) $(DRAFT_IN) $(BIBLIOGRAPHY) $(SYSTEM) $(CITATION_PROTOCOL) $(P_DRAFT) $(TARGET_STYLE) tools/render_prompt.py tools/enforce_protocol.py tools/validate_latex.py tools/llm_run.sh tools/openai_responses.py
	@if [ -z "$(IN)" ]; then echo "IN is required, e.g. make draft IN=outline.md" >&2; exit 1; fi
	@echo "Draft input: $(DRAFT_IN)"
	@$(call RUN_STAGE,draft,$(P_DRAFT),$(DRAFT_IN),tex,$@)

$(SMOOTH_OUT): $(BUILD_DIR) $(DRAFT_OUT) $(BIBLIOGRAPHY) $(SYSTEM) $(CITATION_PROTOCOL) $(P_SMOOTH) $(TARGET_STYLE) tools/render_prompt.py tools/enforce_protocol.py tools/validate_latex.py tools/llm_run.sh tools/openai_responses.py
	@$(call RUN_STAGE,smooth,$(P_SMOOTH),$(DRAFT_OUT),tex,$@)

$(REVISE_OUT): $(BUILD_DIR) $(SMOOTH_OUT) $(BIBLIOGRAPHY) $(SYSTEM) $(CITATION_PROTOCOL) $(P_REVISE) $(TARGET_STYLE) tools/render_prompt.py tools/enforce_protocol.py tools/validate_latex.py tools/llm_run.sh tools/openai_responses.py
	@$(call RUN_STAGE,revise,$(P_REVISE),$(SMOOTH_OUT),tex,$@)

# review: LaTeX in -> structured Markdown diagnostic out
$(REVIEW_OUT): $(BUILD_DIR) $(REVISE_OUT) $(BIBLIOGRAPHY) $(SYSTEM) $(CITATION_PROTOCOL) $(P_REVIEW) $(TARGET_STYLE) tools/render_prompt.py tools/enforce_protocol.py tools/validate_latex.py tools/llm_run.sh tools/openai_responses.py
	@$(call RUN_STAGE,review,$(P_REVIEW),$(REVISE_OUT),md,$@)

# final: validate peer-review authority first. PASS promotes revise.tex without
# another model call; only REVISE_REALISATION may invoke one bounded final pass.
$(FINAL_OUT): $(BUILD_DIR) $(REVISE_OUT) $(REVIEW_OUT) $(BIBLIOGRAPHY) $(SYSTEM) $(CITATION_PROTOCOL) $(P_FINAL) $(TARGET_STYLE) tools/review_decision.py tools/render_prompt.py tools/enforce_protocol.py tools/validate_latex.py tools/llm_run.sh tools/openai_responses.py
	@decision="$$(python tools/review_decision.py \
	  --review "$(REVIEW_OUT)" --revised "$(REVISE_OUT)" \
	  --output "$(FINAL_OUT)" --diagnostic "$(ERROR_DIR)/review.md" \
	  --final-diagnostic "$(ERROR_DIR)/final.md")"; \
	case "$$decision" in \
	  PASS) \
	    ;; \
	  REVISE_REALISATION) \
	    $(call RUN_STAGE,final,$(P_FINAL),$(REVISE_OUT),tex,$@,--review $(REVIEW_OUT)); \
	    ;; \
	  *) \
	    echo "review: unexpected decision '$$decision'" >&2; exit 2; \
	    ;; \
	esac

$(SUMMARY_OUT): $(BUILD_DIR) $(IN) $(BIBLIOGRAPHY) $(SYSTEM) $(CITATION_PROTOCOL) prompts/05_summarize.md $(TARGET_STYLE) tools/render_prompt.py tools/enforce_protocol.py tools/validate_latex.py tools/llm_run.sh tools/openai_responses.py
	@if [ -z "$(IN)" ]; then echo "IN is required, e.g. make summarize IN=outline.md" >&2; exit 1; fi
	@echo "Summarize input: $(IN)"
	@$(call RUN_STAGE,summarize,prompts/05_summarize.md,$(IN),tex,$@)

clean:
	rm -f "$(DRAFT_OUT)" "$(SMOOTH_OUT)" "$(REVISE_OUT)" "$(REVIEW_OUT)" "$(FINAL_OUT)" "$(FINAL_PDF)" "$(SUMMARY_OUT)" "$(BUILD_BIBLIOGRAPHY)" "$(OPENAI_USAGE_LOG)"
	rm -rf "$(ERROR_DIR)"

clobber:
	rm -rf "$(BUILD_DIR)"
