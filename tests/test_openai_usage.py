import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from tools.openai_responses import (
    USAGE_SCHEMA,
    append_usage_record,
    estimate_cost_usd,
    usage_record,
)
from tools.summarize_openai_usage import (
    USAGE_SCHEMA as SUMMARY_USAGE_SCHEMA,
    load_records,
    render_summary,
)

ROOT = Path(__file__).resolve().parents[1]


class OpenAiUsageTests(unittest.TestCase):
    def test_usage_schema_is_shared_by_writer_and_summary_reader(self):
        self.assertEqual(USAGE_SCHEMA, SUMMARY_USAGE_SCHEMA)

    def test_gpt5_mini_cost_uses_cached_input_discount(self):
        estimate = estimate_cost_usd(
            "gpt-5-mini",
            input_tokens=1000,
            cached_input_tokens=400,
            output_tokens=500,
        )
        self.assertEqual(estimate, Decimal("0.001160"))

    def test_supported_snapshots_keep_family_pricing(self):
        estimate = estimate_cost_usd(
            "gpt-5-mini-2025-08-07",
            input_tokens=1_000_000,
            cached_input_tokens=0,
            output_tokens=0,
        )
        self.assertEqual(estimate, Decimal("0.250"))

    def test_unknown_or_new_model_family_does_not_reuse_gpt5_price(self):
        self.assertIsNone(
            estimate_cost_usd(
                "gpt-5.4",
                input_tokens=1000,
                cached_input_tokens=0,
                output_tokens=500,
            )
        )

    def test_usage_record_normalizes_missing_total(self):
        record = usage_record(
            stage="draft",
            model="gpt-5-mini",
            input_tokens=100,
            cached_input_tokens=20,
            output_tokens=30,
            total_tokens=None,
        )
        self.assertEqual(record["schema"], USAGE_SCHEMA)
        self.assertEqual(record["stage"], "draft")
        self.assertEqual(record["total_tokens"], 130)
        self.assertIsNotNone(record["estimated_cost_usd"])

    def test_jsonl_log_round_trips_and_summary_totals_stages(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "build" / "openai-usage.jsonl"
            first = usage_record(
                stage="draft",
                model="gpt-5-mini",
                input_tokens=1000,
                cached_input_tokens=400,
                output_tokens=500,
                total_tokens=1500,
            )
            second = usage_record(
                stage="review",
                model="gpt-5-mini",
                input_tokens=2000,
                cached_input_tokens=1000,
                output_tokens=250,
                total_tokens=2250,
            )
            append_usage_record(path, first)
            append_usage_record(path, second)

            records = load_records(path)
            self.assertEqual([record["stage"] for record in records], ["draft", "review"])
            summary = render_summary(records)
            self.assertIn("## OpenAI compilation usage", summary)
            self.assertIn("| draft | `gpt-5-mini` | 1,000 | 400 | 500 | 1,500 | $0.001160 |", summary)
            self.assertIn("| review | `gpt-5-mini` | 2,000 | 1,000 | 250 | 2,250 | $0.000775 |", summary)
            self.assertIn("| **Total** |  | **3,000** | **1,400** | **750** | **3,750** | **$0.001935** |", summary)

    def test_summary_refuses_to_show_partial_total_for_unpriced_model(self):
        known = usage_record(
            stage="draft",
            model="gpt-5-mini",
            input_tokens=100,
            cached_input_tokens=0,
            output_tokens=10,
            total_tokens=110,
        )
        unknown = usage_record(
            stage="review",
            model="future-model",
            input_tokens=100,
            cached_input_tokens=0,
            output_tokens=10,
            total_tokens=110,
        )
        summary = render_summary([known, unknown])
        self.assertIn("| review | `future-model`", summary)
        self.assertIn("| **Total** |  | **200** | **0** | **20** | **220** | **N/A** |", summary)
        self.assertIn("no potentially misleading partial total", summary)

    def test_missing_log_produces_zero_usage_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = load_records(Path(tmp) / "missing.jsonl")
        self.assertEqual(records, [])
        self.assertIn("No OpenAI usage was recorded", render_summary(records))

    def test_summary_cli_runs_directly_from_repository_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "usage.jsonl"
            append_usage_record(
                path,
                usage_record(
                    stage="draft",
                    model="gpt-5-mini",
                    input_tokens=10,
                    cached_input_tokens=0,
                    output_tokens=5,
                    total_tokens=15,
                ),
            )
            result = subprocess.run(
                [sys.executable, "tools/summarize_openai_usage.py", "--input", str(path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("| draft | `gpt-5-mini`", result.stdout)

    def test_make_routes_stage_and_usage_log_to_openai_adapter(self):
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("OPENAI_USAGE_LOG ?= $(BUILD_DIR)/openai-usage.jsonl", makefile)
        self.assertIn("COMPILED_PROSE_STAGE=$(1)", makefile)
        self.assertIn('OPENAI_USAGE_LOG="$(OPENAI_USAGE_LOG)"', makefile)

    def test_malformed_log_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "usage.jsonl"
            path.write_text(json.dumps({"schema": "wrong"}) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported schema"):
                load_records(path)


if __name__ == "__main__":
    unittest.main()
