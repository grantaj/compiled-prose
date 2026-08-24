#!/usr/bin/env python3
import json
import os
import re
import sys
from decimal import Decimal
from pathlib import Path
from typing import Optional


USAGE_SCHEMA = "compiled-prose-openai-usage/1"
ACADEMIC_REVIEW_STAGE = "prompts/40_peer_review.md"
ACADEMIC_JOURNAL_TARGET = "prompts/targets/journal_academic.md"

# Standard API text-token pricing verified 2026-08-21.
# Values are USD per 1M tokens: input, cached input, output.
# GPT-5.6 requests above 272K input tokens use the provider's published
# long-context multipliers: 2x input/cached-input and 1.5x output.
_GPT56_PATTERN = re.compile(r"^gpt-5\.6-(?:luna|terra|sol)$")
_GPT56_LONG_CONTEXT_THRESHOLD = 272_000
_PRICING = (
    (
        re.compile(r"^gpt-5\.6-luna$"),
        (Decimal("0.200"), Decimal("0.020"), Decimal("1.200")),
    ),
    (
        re.compile(r"^gpt-5\.6-terra$"),
        (Decimal("2.000"), Decimal("0.200"), Decimal("12.000")),
    ),
    (
        re.compile(r"^gpt-5\.6-sol$"),
        (Decimal("5.000"), Decimal("0.500"), Decimal("30.000")),
    ),
    (
        re.compile(r"^gpt-5-mini(?:-\d{4}-\d{2}-\d{2})?$"),
        (Decimal("0.250"), Decimal("0.025"), Decimal("2.000")),
    ),
    (
        re.compile(r"^gpt-5(?:-\d{4}-\d{2}-\d{2})?$"),
        (Decimal("1.250"), Decimal("0.125"), Decimal("10.000")),
    ),
)


def response_tool_kwargs(*, stage: str, target: str) -> dict:
    """Return provider tools for the one intentionally open-world review case."""
    if stage == ACADEMIC_REVIEW_STAGE and target == ACADEMIC_JOURNAL_TARGET:
        return {
            "tools": [{"type": "web_search"}],
            # With only one configured tool, `required` guarantees that academic
            # peer review actually performs external search at least once.
            "tool_choice": "required",
        }
    return {}


def pricing_for_model(model: str):
    for pattern, pricing in _PRICING:
        if pattern.fullmatch(model):
            return pricing
    return None


def estimate_cost_usd(
    model: str,
    *,
    input_tokens: int,
    cached_input_tokens: int,
    output_tokens: int,
) -> Optional[Decimal]:
    pricing = pricing_for_model(model)
    if pricing is None:
        return None
    input_per_million, cached_per_million, output_per_million = pricing
    cached = max(cached_input_tokens, 0)
    uncached = max(input_tokens - cached, 0)
    input_multiplier = Decimal("1")
    output_multiplier = Decimal("1")
    if (
        _GPT56_PATTERN.fullmatch(model)
        and input_tokens > _GPT56_LONG_CONTEXT_THRESHOLD
    ):
        input_multiplier = Decimal("2")
        output_multiplier = Decimal("1.5")
    million = Decimal(1_000_000)
    return (
        Decimal(uncached) * input_per_million * input_multiplier
        + Decimal(cached) * cached_per_million * input_multiplier
        + Decimal(output_tokens) * output_per_million * output_multiplier
    ) / million


def usage_record(
    *,
    stage: str,
    model: str,
    input_tokens: int,
    cached_input_tokens: int,
    output_tokens: int,
    total_tokens: Optional[int],
) -> dict:
    estimate = estimate_cost_usd(
        model,
        input_tokens=input_tokens,
        cached_input_tokens=cached_input_tokens,
        output_tokens=output_tokens,
    )
    pricing = pricing_for_model(model)
    normalized_total = (
        total_tokens if total_tokens is not None else input_tokens + output_tokens
    )
    record = {
        "schema": USAGE_SCHEMA,
        "stage": stage,
        "model": model,
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": normalized_total,
        "estimated_cost_usd": str(estimate) if estimate is not None else None,
    }
    if pricing is not None:
        record["pricing_usd_per_million"] = {
            "input": str(pricing[0]),
            "cached_input": str(pricing[1]),
            "output": str(pricing[2]),
        }
    return record


def append_usage_record(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def main():
    # Keep the provider SDK optional for keyless/Ollama use. Import it only when
    # this adapter is actually invoked.
    from openai import OpenAI

    prompt = sys.stdin.read()

    model = os.environ.get("OPENAI_MODEL", "gpt-5")
    temperature_raw = os.environ.get("OPENAI_TEMPERATURE")
    temperature = float(temperature_raw) if temperature_raw is not None else None
    seed = os.environ.get("OPENAI_SEED")
    seed = int(seed) if seed is not None else None
    max_output = os.environ.get("OPENAI_MAX_OUTPUT_TOKENS")
    max_output = int(max_output) if max_output is not None else None
    stage = os.environ.get("COMPILED_PROSE_STAGE", "unknown")
    target = os.environ.get("COMPILED_PROSE_TARGET", "")

    client = OpenAI()

    kwargs = {"model": model, "input": prompt}
    kwargs.update(response_tool_kwargs(stage=stage, target=target))
    no_temp_prefixes = ("gpt-5",)
    if temperature is not None and not model.startswith(no_temp_prefixes):
        kwargs["temperature"] = temperature
    if seed is not None:
        # The Responses API does not accept 'seed'; ignore if set to avoid errors.
        pass
    if max_output is not None:
        kwargs["max_output_tokens"] = max_output

    resp = client.responses.create(**kwargs)
    sys.stdout.write(resp.output_text)

    reason = getattr(resp, "finish_reason", None)
    if reason:
        sys.stderr.write(f"\n[openai] finish_reason={reason}\n")

    usage = getattr(resp, "usage", None)
    if usage:
        input_tokens = getattr(usage, "input_tokens", None)
        output_tokens = getattr(usage, "output_tokens", None)
        total_tokens = getattr(usage, "total_tokens", None)
        details = getattr(usage, "input_tokens_details", None)
        cached_tokens = getattr(details, "cached_tokens", None) if details else None
        sys.stderr.write(
            f"[openai] tokens input={input_tokens} output={output_tokens} total={total_tokens} cached_input={cached_tokens}\n"
        )

        if input_tokens is not None and output_tokens is not None:
            record = usage_record(
                stage=stage,
                model=model,
                input_tokens=input_tokens,
                cached_input_tokens=cached_tokens or 0,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
            )
            estimate = record["estimated_cost_usd"]
            if estimate is not None:
                sys.stderr.write(f"[openai] est_cost_usd={Decimal(estimate):.6f}\n")
            else:
                sys.stderr.write(
                    f"[openai] est_cost_usd=unavailable model={model!r} pricing_not_configured\n"
                )

            usage_log = os.environ.get("OPENAI_USAGE_LOG")
            if usage_log:
                try:
                    append_usage_record(Path(usage_log), record)
                except OSError as exc:
                    # The paid request has already completed. Do not turn a usage-log
                    # filesystem problem into a retryable provider failure.
                    sys.stderr.write(
                        f"[openai] warning: could not append usage log {usage_log!r}: {exc}\n"
                    )


if __name__ == "__main__":
    main()
