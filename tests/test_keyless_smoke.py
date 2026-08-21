import ast
import importlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.enforce_protocol import enforce_result

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "tiny_outline.md"


class KeylessSmokeTests(unittest.TestCase):
    def test_python_helpers_import_without_optional_provider_packages(self):
        for path in sorted((ROOT / "tools").glob("*.py")):
            module_name = f"tools.{path.stem}"
            with self.subTest(module=module_name):
                importlib.import_module(module_name)

    def test_python_sources_parse_as_supported_python_39(self):
        paths = sorted((ROOT / "tools").glob("*.py")) + sorted(
            (ROOT / "tests").glob("*.py")
        )
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT)):
                ast.parse(
                    path.read_text(encoding="utf-8"),
                    filename=str(path),
                    feature_version=(3, 9),
                )

    def test_prompt_renderer_cli_uses_tiny_owned_fixture(self):
        result = subprocess.run(
            [
                sys.executable,
                "tools/render_prompt.py",
                "--system",
                "prompts/00_system.md",
                "--stage",
                "prompts/10_draft.md",
                "--target",
                "prompts/targets/journal_academic.md",
                "--source",
                str(FIXTURE),
                "--in",
                str(FIXTURE),
                "--output-type",
                "tex",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(FIXTURE.read_text(encoding="utf-8").strip(), result.stdout)
        self.assertEqual(result.stdout.count("OUTPUT_TYPE: tex"), 1)
        self.assertNotIn("forgotten-stuff", result.stdout)

    def test_nominal_success_cannot_mix_failure_sentinel(self):
        cases = (
            (
                "tex",
                "\\documentclass{article}\n\\begin{document}\n@@FAIL\n\\end{document}\n",
            ),
            ("md", "# Review\n\n@@FAIL\n\nUnexpected mixed result.\n"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for index, (output_type, raw) in enumerate(cases):
                with self.subTest(output_type=output_type):
                    output = root / f"out-{index}"
                    diagnostic = root / "errors" / f"out-{index}.md"
                    success = enforce_result(
                        raw,
                        stage="smoke",
                        output_type=output_type,
                        output=output,
                        diagnostic=diagnostic,
                    )
                    self.assertFalse(success)
                    self.assertFalse(output.exists())
                    self.assertIn(
                        "mixed the `@@FAIL` failure sentinel",
                        diagnostic.read_text(encoding="utf-8"),
                    )

    def test_make_check_aggregates_only_keyless_targets(self):
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        target = next(
            line.strip() for line in makefile.splitlines() if line.startswith("check:")
        )
        self.assertEqual(target, "check: check-python check-shell test")

    def test_openai_requirement_declares_responses_api_floor(self):
        requirements = {
            line.strip()
            for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        self.assertIn("openai>=1.66.3", requirements)


if __name__ == "__main__":
    unittest.main()
