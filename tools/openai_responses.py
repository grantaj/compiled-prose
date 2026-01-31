#!/usr/bin/env python3
import os, sys
from openai import OpenAI

def main():
    prompt = sys.stdin.read()

    model = os.environ.get("OPENAI_MODEL", "gpt-5")
    temperature_raw = os.environ.get("OPENAI_TEMPERATURE")
    temperature = float(temperature_raw) if temperature_raw is not None else None
    seed = os.environ.get("OPENAI_SEED")
    seed = int(seed) if seed is not None else None
    max_output = os.environ.get("OPENAI_MAX_OUTPUT_TOKENS")
    max_output = int(max_output) if max_output is not None else None

    client = OpenAI()

    kwargs = {"model": model, "input": prompt}
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

        # Cost estimates based on current pricing.
        # gpt-5: input $1.250 / 1M, cached input $0.125 / 1M, output $10.000 / 1M
        # gpt-5-mini: input $0.250 / 1M, cached input $0.025 / 1M, output $2.000 / 1M
        if input_tokens is not None and output_tokens is not None:
            cached = cached_tokens or 0
            uncached = max(input_tokens - cached, 0)
            if model.startswith("gpt-5-mini"):
                in_rate = 0.250 / 1_000_000
                cached_rate = 0.025 / 1_000_000
                out_rate = 2.000 / 1_000_000
            elif model.startswith("gpt-5"):
                in_rate = 1.250 / 1_000_000
                cached_rate = 0.125 / 1_000_000
                out_rate = 10.000 / 1_000_000
            else:
                in_rate = cached_rate = out_rate = None

            if in_rate is not None:
                est = uncached * in_rate + cached * cached_rate + output_tokens * out_rate
                sys.stderr.write(f"[openai] est_cost_usd={est:.6f}\n")

if __name__ == "__main__":
    main()
