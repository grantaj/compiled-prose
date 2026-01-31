SHELL := /usr/bin/env bash
.SHELLFLAGS := -euo pipefail -c

# Load .env outside of Make (e.g., export vars in your shell) if needed.

BUILD_DIR := build

# Backend selection (can be overridden: make BACKEND=openai final)
BACKEND ?= ollama

# OpenAI config
OPENAI_MODEL ?= gpt-5
OPENAI_TEMPERATURE ?= 0.2
OPENAI_SEED ?= 42

# Ollama config
OLLAMA_MODEL ?= llama3.1
OLLAMA_HOST ?= http://localhost:11434

# Inputs
IN ?=
SYSTEM := prompts/00_system.md
TARGET_STYLE ?= prompts/targets/journal_academic.md
SUMMARY_IN ?= $(OUTLINE)
IN ?= $(SUMMARY_IN)

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
SUMMARY_OUT := $(BUILD_DIR)/summary.tex

.PHONY: all draft smooth revise review final summarize check-ollama openai-check print-vars clean clobber
all: final
draft: $(DRAFT_OUT)
smooth: $(SMOOTH_OUT)
revise: $(REVISE_OUT)
review: $(REVIEW_OUT)
final: $(FINAL_OUT)
summarize: $(SUMMARY_OUT)

check-ollama:
	@python tools/check_ollama.py

openai-check:
	@printf 'ping' | BACKEND=openai OPENAI_MODEL=$(OPENAI_MODEL) \
	  python tools/openai_responses.py >/dev/null && \
	echo "OpenAI OK" || \
	( echo "OpenAI request failed; check API key and billing." >&2; exit 1 )

print-vars:
	@echo "OUTLINE=$(OUTLINE)"
	@echo "IN=$(IN)"
	@echo "SUMMARY_IN=$(SUMMARY_IN)"
	@echo "MAKEFLAGS=$(MAKEFLAGS)"


$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

define RUN_LLM
python tools/render_prompt.py \
  --system $(SYSTEM) --stage $(1) --target $(TARGET_STYLE) --in $(2) $(3) \
| BACKEND=$(BACKEND) \
  OPENAI_MODEL=$(OPENAI_MODEL) OPENAI_TEMPERATURE=$(OPENAI_TEMPERATURE) OPENAI_SEED=$(OPENAI_SEED) \
  OLLAMA_MODEL=$(OLLAMA_MODEL) OLLAMA_HOST=$(OLLAMA_HOST) \
  bash tools/llm_run.sh
endef

ifndef IN
$(error IN is required, e.g. make draft IN=example_outline.md)
endif

DRAFT_IN := $(IN)

$(DRAFT_OUT): $(BUILD_DIR) $(DRAFT_IN) $(SYSTEM) $(P_DRAFT) $(TARGET_STYLE) tools/render_prompt.py tools/llm_run.sh tools/openai_responses.py
	@echo "Draft input: $(DRAFT_IN)"
	$(call RUN_LLM,$(P_DRAFT),$(DRAFT_IN),) > "$@"

$(SMOOTH_OUT): $(BUILD_DIR) $(DRAFT_OUT) $(SYSTEM) $(P_SMOOTH) $(TARGET_STYLE) tools/render_prompt.py tools/llm_run.sh tools/openai_responses.py
	$(call RUN_LLM,$(P_SMOOTH),$(DRAFT_OUT),) > "$@"

$(REVISE_OUT): $(BUILD_DIR) $(SMOOTH_OUT) $(SYSTEM) $(P_REVISE) $(TARGET_STYLE) tools/render_prompt.py tools/llm_run.sh tools/openai_responses.py
	$(call RUN_LLM,$(P_REVISE),$(SMOOTH_OUT),) > "$@"

# review: LaTeX in → Markdown out
$(REVIEW_OUT): $(BUILD_DIR) $(REVISE_OUT) $(SYSTEM) $(P_REVIEW) $(TARGET_STYLE) tools/render_prompt.py tools/llm_run.sh tools/openai_responses.py
	$(call RUN_LLM,$(P_REVIEW),$(REVISE_OUT),) > "$@"

# final: LaTeX in + peer_review.md context → LaTeX out
$(FINAL_OUT): $(BUILD_DIR) $(REVISE_OUT) $(REVIEW_OUT) $(SYSTEM) $(P_FINAL) $(TARGET_STYLE) tools/render_prompt.py tools/llm_run.sh tools/openai_responses.py
	$(call RUN_LLM,$(P_FINAL),$(REVISE_OUT),--review $(REVIEW_OUT)) > "$@"

$(SUMMARY_OUT): $(BUILD_DIR) $(IN) $(SYSTEM) prompts/05_summarize.md $(TARGET_STYLE) tools/render_prompt.py tools/llm_run.sh tools/openai_responses.py
	@echo "Summarize input: $(IN)"
	python tools/render_prompt.py --system $(SYSTEM) --stage prompts/05_summarize.md --target $(TARGET_STYLE) --in $(IN) \
	| BACKEND=$(BACKEND) \
	  OPENAI_MODEL=$(OPENAI_MODEL) OPENAI_TEMPERATURE=$(OPENAI_TEMPERATURE) OPENAI_SEED=$(OPENAI_SEED) \
	  OLLAMA_MODEL=$(OLLAMA_MODEL) OLLAMA_HOST=$(OLLAMA_HOST) \
	  bash tools/llm_run.sh > "$@"

clean:
	rm -f $(DRAFT_OUT) $(SMOOTH_OUT) $(REVISE_OUT) $(REVIEW_OUT) $(FINAL_OUT) $(SUMMARY_OUT)

clobber:
	rm -rf $(BUILD_DIR)
