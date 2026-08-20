import ast
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENFORCER = ROOT / "tools" / "enforce_protocol.py"


class EnforceProtocolTests(unittest.TestCase):
    def run_enforcer(
        self,
        raw: str,
        output: Path,
        diagnostic: Path,
        stage: str = "draft",
        output_type: str = "tex",
        backend_exit_status=None,
    ):
        command = [
            sys.executable,
            str(ENFORCER),
            "--stage",
            stage,
            "--output-type",
            output_type,
            "--output",
            str(output),
            "--diagnostic",
            str(diagnostic),
        ]
        if backend_exit_status is not None:
            command.extend(["--backend-exit-status", str(backend_exit_status)])
        return subprocess.run(
            command,
            input=raw,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_success_outputs_are_published_for_tex_and_markdown(self):
        cases = (
            (
                "draft",
                "tex",
                "\\documentclass{article}\n\\begin{document}ok\\end{document}\n",
                "draft.tex",
            ),
            ("review", "md", "# Review\n\nNo blocking issues.\n", "peer_review.md"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp)
            for stage, output_type, raw, name in cases:
                with self.subTest(stage=stage):
                    output = build / name
                    diagnostic = build / "errors" / f"{stage}.md"
                    diagnostic.parent.mkdir(parents=True, exist_ok=True)
                    diagnostic.write_text("stale error", encoding="utf-8")

                    result = self.run_enforcer(
                        raw,
                        output,
                        diagnostic,
                        stage=stage,
                        output_type=output_type,
                    )

                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(output.read_text(encoding="utf-8"), raw)
                    self.assertFalse(diagnostic.exists())

    def test_fail_sentinel_writes_external_diagnostic_and_removes_stale_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "custom-build"
            output = build / "draft.tex"
            diagnostic = build / "errors" / "draft.md"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("old successful artefact", encoding="utf-8")
            raw = "@@FAIL\n# Blocking issues\n\n- Section 2 lacks an authored warrant.\n"

            result = self.run_enforcer(raw, output, diagnostic)

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())
            self.assertEqual(
                diagnostic.read_text(encoding="utf-8"),
                "# Blocking issues\n\n- Section 2 lacks an authored warrant.\n",
            )
            self.assertNotIn("@@FAIL", diagnostic.read_text(encoding="utf-8"))
            self.assertIn(str(diagnostic), result.stderr)

    def test_empty_or_malformed_failure_output_fails_closed(self):
        cases = ("", "\n@@FAIL\n# Blocking issues\n- gap\n")
        with tempfile.TemporaryDirectory() as tmp:
            for index, raw in enumerate(cases):
                with self.subTest(raw=raw):
                    output = Path(tmp) / f"out-{index}.tex"
                    diagnostic = Path(tmp) / "errors" / f"out-{index}.md"
                    result = self.run_enforcer(raw, output, diagnostic)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(output.exists())
                    self.assertIn("# Protocol error", diagnostic.read_text(encoding="utf-8"))

    def test_declared_success_type_is_enforced(self):
        cases = (
            (
                "tex",
                "# Blocking issues\n\n- This is Markdown, not LaTeX.\n",
                "complete raw LaTeX document",
            ),
            (
                "tex",
                "```latex\n\\documentclass{article}\n\\begin{document}ok\\end{document}\n```\n",
                "complete raw LaTeX document",
            ),
            (
                "md",
                "\\documentclass{article}\n\\begin{document}ok\\end{document}\n",
                "where Markdown was declared",
            ),
        )
        with tempfile.TemporaryDirectory() as tmp:
            for index, (output_type, raw, expected) in enumerate(cases):
                with self.subTest(output_type=output_type, raw=raw):
                    output = Path(tmp) / f"out-{index}"
                    diagnostic = Path(tmp) / "errors" / f"out-{index}.md"
                    result = self.run_enforcer(
                        raw,
                        output,
                        diagnostic,
                        output_type=output_type,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(output.exists())
                    self.assertIn(expected, diagnostic.read_text(encoding="utf-8"))

    def test_backend_failure_replaces_stale_diagnostic(self):
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp)
            output = build / "draft.tex"
            diagnostic = build / "errors" / "draft.md"
            diagnostic.parent.mkdir(parents=True)
            output.write_text("stale output", encoding="utf-8")
            diagnostic.write_text("stale source diagnostic", encoding="utf-8")

            result = self.run_enforcer(
                "partial output",
                output,
                diagnostic,
                backend_exit_status=3,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())
            text = diagnostic.read_text(encoding="utf-8")
            self.assertIn("exited with status 3", text)
            self.assertIn("partial output was discarded", text)
            self.assertNotIn("stale source diagnostic", text)

    def test_enforcer_remains_python_39_compatible(self):
        ast.parse(
            ENFORCER.read_text(encoding="utf-8"),
            filename=str(ENFORCER),
            feature_version=(3, 9),
        )


class MakefileProtocolIntegrationTests(unittest.TestCase):
    def write_runner(self, path: Path, body: str) -> None:
        path.write_text(
            "#!/usr/bin/env bash\nset -euo pipefail\ncat >/dev/null\n" + body,
            encoding="utf-8",
        )

    def run_make(self, build: Path, outline: Path, runner: Path):
        return subprocess.run(
            [
                "make",
                "-B",
                "draft",
                f"IN={outline}",
                f"BUILD_DIR={build}",
                f"LLM_RUNNER=bash {runner}",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_make_failure_is_nonzero_external_and_build_dir_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build = root / "build-experiment"
            build.mkdir()
            outline = root / "outline.md"
            outline.write_text("# Under-specified\n- Claim with no warrant\n", encoding="utf-8")
            runner = root / "fake-llm.sh"
            self.write_runner(
                runner,
                "printf '%s\\n' '@@FAIL' '# Blocking issues' '' '- Missing authored warrant.'\n",
            )
            stale = build / "draft.tex"
            stale.write_text("old successful artefact", encoding="utf-8")

            result = self.run_make(build, outline, runner)

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(stale.exists())
            diagnostic = build / "errors" / "draft.md"
            self.assertTrue(diagnostic.exists())
            self.assertIn("Missing authored warrant", diagnostic.read_text(encoding="utf-8"))
            self.assertFalse((ROOT / "build" / "errors" / "draft.md").exists())

    def test_make_rejects_wrong_declared_success_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build = root / "build-wrong-type"
            build.mkdir()
            outline = root / "outline.md"
            outline.write_text("# Input\n- claim\n", encoding="utf-8")
            runner = root / "fake-llm.sh"
            self.write_runner(runner, "printf '%s\\n' '# Explanation' '' 'Could not draft this.'\n")

            result = self.run_make(build, outline, runner)

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((build / "draft.tex").exists())
            diagnostic = build / "errors" / "draft.md"
            self.assertIn(
                "complete raw LaTeX document",
                diagnostic.read_text(encoding="utf-8"),
            )

    def test_backend_process_failure_cannot_publish_partial_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build = root / "build-provider-failure"
            build.mkdir()
            outline = root / "outline.md"
            outline.write_text("# Input\n- claim\n", encoding="utf-8")
            runner = root / "fake-llm.sh"
            self.write_runner(runner, "printf 'partial latex'\nexit 3\n")
            stale = build / "draft.tex"
            stale.write_text("old successful artefact", encoding="utf-8")
            diagnostic = build / "errors" / "draft.md"
            diagnostic.parent.mkdir(parents=True)
            diagnostic.write_text("stale source diagnostic", encoding="utf-8")

            result = self.run_make(build, outline, runner)

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(stale.exists())
            diagnostic_text = diagnostic.read_text(encoding="utf-8")
            self.assertIn("exited with status 3", diagnostic_text)
            self.assertIn("partial output was discarded", diagnostic_text)
            self.assertNotIn("stale source diagnostic", diagnostic_text)

    def test_successful_rebuild_publishes_output_and_clears_old_diagnostic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build = root / "build-success"
            build.mkdir()
            outline = root / "outline.md"
            outline.write_text("# Sufficient\n- supported claim\n", encoding="utf-8")
            runner = root / "fake-llm.sh"
            self.write_runner(
                runner,
                "printf '%s\\n' '\\documentclass{article}' '\\begin{document}ok\\end{document}'\n",
            )
            diagnostic = build / "errors" / "draft.md"
            diagnostic.parent.mkdir(parents=True)
            diagnostic.write_text("stale failure", encoding="utf-8")

            result = self.run_make(build, outline, runner)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("\\documentclass{article}", (build / "draft.tex").read_text(encoding="utf-8"))
            self.assertFalse(diagnostic.exists())


if __name__ == "__main__":
    unittest.main()
