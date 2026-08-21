import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALID_TEX_A = "\\documentclass{article}\n\\begin{document}alpha\\end{document}\n"
VALID_TEX_B = "\\documentclass{article}\n\\begin{document}beta\\end{document}\n"
GENERATED = (
    "draft.tex",
    "smooth.tex",
    "revise.tex",
    "peer_review.md",
    "final.tex",
    "final.pdf",
    "summary.tex",
    "references.bib",
)


class BuildDirectoryIsolationTests(unittest.TestCase):
    def run_make(self, *args: str, env=None):
        return subprocess.run(
            ["make", "--no-print-directory", *args],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_default_and_overridden_paths_cover_all_generated_outputs(self):
        default_env = os.environ.copy()
        default_env.pop("BUILD_DIR", None)
        default = self.run_make("-n", "-B", "IN=outline.md", "draft", env=default_env)
        self.assertEqual(default.returncode, 0, default.stderr)
        self.assertIn('"build/draft.tex"', default.stdout)
        self.assertIn('"build/errors/draft.md"', default.stdout)

        alternate = self.run_make(
            "-n", "-B", "BUILD_DIR=build-test-a", "IN=outline.md", "final", "summarize"
        )
        self.assertEqual(alternate.returncode, 0, alternate.stderr)
        for path in GENERATED[:-1]:
            self.assertIn(f"build-test-a/{path}", alternate.stdout)
        for stage in ("draft", "smooth", "revise", "review", "final", "summarize"):
            self.assertIn(f"build-test-a/errors/{stage}.md", alternate.stdout)

    def test_environment_can_override_default_build_directory(self):
        env = os.environ.copy()
        env["BUILD_DIR"] = "build-env"
        result = self.run_make("-n", "-B", "IN=outline.md", "draft", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"build-env/draft.tex"', result.stdout)
        self.assertIn('"build-env/errors/draft.md"', result.stdout)

    def test_two_builds_coexist_and_failure_diagnostics_are_isolated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.md"
            source.write_text("# Source\n", encoding="utf-8")
            runner = root / "fake-runner.sh"
            runner.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "cat >/dev/null\n"
                'cat "$FAKE_OUTPUT_FILE"\n',
                encoding="utf-8",
            )
            runner.chmod(0o755)

            first_output = root / "first.out"
            first_output.write_text(VALID_TEX_A, encoding="utf-8")
            second_output = root / "second.out"
            second_output.write_text(VALID_TEX_B, encoding="utf-8")
            failure_output = root / "failure.out"
            failure_output.write_text("@@FAIL\n# Missing source detail\n", encoding="utf-8")
            build_a = root / "build-test-a"
            build_b = root / "build-test-b"

            env = os.environ.copy()
            env["FAKE_OUTPUT_FILE"] = str(first_output)
            first = self.run_make(
                f"BUILD_DIR={build_a}", f"IN={source}", f"LLM_RUNNER={runner}", "draft", env=env
            )
            self.assertEqual(first.returncode, 0, first.stderr)

            env["FAKE_OUTPUT_FILE"] = str(second_output)
            second = self.run_make(
                f"BUILD_DIR={build_b}", f"IN={source}", f"LLM_RUNNER={runner}", "draft", env=env
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual((build_a / "draft.tex").read_text(encoding="utf-8"), VALID_TEX_A)
            self.assertEqual((build_b / "draft.tex").read_text(encoding="utf-8"), VALID_TEX_B)

            env["FAKE_OUTPUT_FILE"] = str(failure_output)
            failed = self.run_make(
                "-B", f"BUILD_DIR={build_b}", f"IN={source}", f"LLM_RUNNER={runner}", "draft", env=env
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual((build_a / "draft.tex").read_text(encoding="utf-8"), VALID_TEX_A)
            self.assertFalse((build_b / "draft.tex").exists())
            self.assertIn(
                "Missing source detail",
                (build_b / "errors" / "draft.md").read_text(encoding="utf-8"),
            )

    def test_clean_and_clobber_only_touch_selected_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_a = root / "build-test-a"
            build_b = root / "build-test-b"
            for build in (build_a, build_b):
                (build / "errors").mkdir(parents=True)
                for name in GENERATED:
                    (build / name).write_text(name, encoding="utf-8")
                (build / "errors" / "draft.md").write_text("diagnostic", encoding="utf-8")
                (build / "keep.txt").write_text("unknown", encoding="utf-8")

            clean = self.run_make(f"BUILD_DIR={build_a}", "clean")
            self.assertEqual(clean.returncode, 0, clean.stderr)
            self.assertTrue(build_a.exists())
            self.assertTrue((build_a / "keep.txt").exists())
            for name in GENERATED:
                self.assertFalse((build_a / name).exists())
            self.assertFalse((build_a / "errors").exists())
            self.assertTrue((build_b / "draft.tex").exists())
            self.assertTrue((build_b / "errors" / "draft.md").exists())

            clobber = self.run_make(f"BUILD_DIR={build_a}", "clobber")
            self.assertEqual(clobber.returncode, 0, clobber.stderr)
            self.assertFalse(build_a.exists())
            self.assertTrue((build_b / "draft.tex").exists())
            self.assertTrue((build_b / "keep.txt").exists())

    def test_gitignore_uses_narrow_root_build_convention(self):
        ignored = ("build/draft.tex", "build-academic/final.tex", "build-test-a/errors/draft.md")
        visible = ("builder/outline.md", "building/notes.md", "notes/build-test-a/source.md")
        for path in ignored:
            result = subprocess.run(
                ["git", "check-ignore", "--no-index", "-q", path], cwd=ROOT, check=False
            )
            self.assertEqual(result.returncode, 0, path)
        for path in visible:
            result = subprocess.run(
                ["git", "check-ignore", "--no-index", "-q", path], cwd=ROOT, check=False
            )
            self.assertEqual(result.returncode, 1, path)


if __name__ == "__main__":
    unittest.main()
