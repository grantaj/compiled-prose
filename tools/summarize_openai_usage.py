#!/usr/bin/env python3
"""Render recorded OpenAI token usage as a GitHub-friendly Markdown summary."""

import argparse
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable


USAGE_SCHEMA = "compiled-prose-openai-usage/1"


def _escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _integer(record: dict, key: str) -> int:
    value = record.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"usage record has invalid {key}: {value!r}")
    return value


def load_records(path: Path) -> list[dict]:
    if not path.is_file():
        return []

    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON on usage-log line {line_number}: {exc}") from exc
        if not isinstance(record, dict):
            raise ValueError(f"usage-log line {line_number} is not an object")
        if record.get("schema") != USAGE_SCHEMA:
            raise ValueError(
                f"usage-log line {line_number} has unsupported schema: {record.get('schema')!r}"
            )
        for key in ("stage", "model"):
            if not isinstance(record.get(key), str) or not record[key]:
                raise ValueError(f"usage-log line {line_number} has invalid {key}")
        for key in (
            "input_tokens",
            "cached_input_tokens",
            "output_tokens",
            "total_tokens",
        ):
            _integer(record, key)
        estimate = record.get("estimated_cost_usd")
        if estimate is not None:
            try:
                if Decimal(str(estimate)) < 0:
                    raise ValueError
            except (InvalidOperation, ValueError) as exc:
                raise ValueError(
                    f"usage-log line {line_number} has invalid estimated_cost_usd"
                ) from exc
        records.append(record)
    return records


def render_summary(records: Iterable[dict]) -> str:
    rows = list(records)
    lines = ["## OpenAI compilation usage", ""]
    if not rows:
        lines.extend(
            [
                "No OpenAI usage was recorded for this run.",
                "",
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
            "| Stage | Model | Input | Cached input | Output | Total | Est. cost (USD) |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    total_input = 0
    total_cached = 0
    total_output = 0
    total_tokens = 0
    total_cost = Decimal("0")
    all_costs_known = True

    for record in rows:
        input_tokens = _integer(record, "input_tokens")
        cached_tokens = _integer(record, "cached_input_tokens")
        output_tokens = _integer(record, "output_tokens")
        row_total = _integer(record, "total_tokens")
        estimate = record.get("estimated_cost_usd")

        total_input += input_tokens
        total_cached += cached_tokens
        total_output += output_tokens
        total_tokens += row_total

        if estimate is None:
            cost_text = "N/A"
            all_costs_known = False
        else:
            cost = Decimal(str(estimate))
            total_cost += cost
            cost_text = f"${cost:.6f}"

        lines.append(
            "| {stage} | `{model}` | {input:,} | {cached:,} | {output:,} | {total:,} | {cost} |".format(
                stage=_escape(record["stage"]),
                model=_escape(record["model"]),
                input=input_tokens,
                cached=cached_tokens,
                output=output_tokens,
                total=row_total,
                cost=cost_text,
            )
        )

    total_cost_text = f"**${total_cost:.6f}**" if all_costs_known else "**N/A**"
    lines.append(
        f"| **Total** |  | **{total_input:,}** | **{total_cached:,}** | "
        f"**{total_output:,}** | **{total_tokens:,}** | {total_cost_text} |"
    )
    lines.extend(
        [
            "",
            "Costs are estimates from API-reported token usage and the pricing table embedded in the compiler; they are not billing records.",
        ]
    )
    if not all_costs_known:
        lines.append(
            "At least one model has no configured pricing, so no potentially misleading partial total is shown."
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    try:
        records = load_records(args.input)
    except (OSError, ValueError) as exc:
        print(f"OpenAI usage summary failed: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(render_summary(records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
