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
                "prompts/10_realise.md",
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

    def test_whitespace_only_success_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for index, output_type in enumerate(("tex", "md")):
                with self.subTest(output_type=output_type):
                    output = root / f"empty-{index}"
                    diagnostic = root / "errors" / f"empty-{index}.md"
                    success = enforce_result(
                        "\ufeff \r\n\t",
                        stage="smoke",
                        output_type=output_type,
                        output=output,
                        diagnostic=diagnostic,
                    )
                    self.assertFalse(success)
                    self.assertFalse(output.exists())
                    self.assertIn(
                        "returned empty output",
                        diagnostic.read_text(encoding="utf-8"),
                    )

    def test_make_check_aggregates_only_keyless_targets(self):
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        target = next(
            line.strip() for line in makefile.splitlines() if line.startswith("check:")
        )
        dependencies = set(target.partition(":")[2].split())
        self.assertEqual(
            dependencies,
            {"check-python", "check-shell", "test", "self-preflight"},
        )

    def test_self_enables_fail_fast_latex_stage_validation(self):
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("VALIDATE_LATEX_STAGES ?= 0", makefile)
        self_compile = next(
            line
            for line in makefile.splitlines()
            if 'BIBLIOGRAPHY="$(BUILD_BIBLIOGRAPHY)" final' in line
        )
        self.assertIn("VALIDATE_LATEX_STAGES=1", self_compile)
        self.assertIn(
            'if [ "$(VALIDATE_LATEX_STAGES)" = "1" ] && [ "$(4)" = "tex" ]; then',
            makefile,
        )
        self.assertIn("python tools/validate_latex.py", makefile)

    def test_openai_requirement_declares_responses_api_floor(self):
        requirements = [
            line.strip()
            for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        declaration = next(line for line in requirements if line.startswith("openai>="))
        version = tuple(int(part) for part in declaration.removeprefix("openai>=").split("."))
        self.assertGreaterEqual(version, (1, 66, 3))


if __name__ == "__main__":
    unittest.main()
