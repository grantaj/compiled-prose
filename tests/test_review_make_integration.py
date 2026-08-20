import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALID_REVISED = (
    "\\documentclass{article}\n"
    "\\begin{document}\n"
    "Revised authored prose.\n"
    "\\end{document}\n"
)
FAKE_FINAL = (
    "\\documentclass{article}\n"
    "\\begin{document}\n"
    "One bounded realisation revision.\n"
    "\\end{document}\n"
)


class ReviewMakeIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.build = self.root / "build"
        self.build.mkdir()
        self.source = self.root / "source.md"
        self.source.write_text("# Source\n- Authored claim\n", encoding="utf-8")
        for name in ("draft.tex", "smooth.tex", "revise.tex"):
            (self.build / name).write_text(VALID_REVISED, encoding="utf-8")

        self.calls = self.root / "runner-calls.txt"
        self.runner = self.root / "fake-runner.sh"
        self.runner.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "cat >/dev/null\n"
            f"printf 'called\\n' >> '{self.calls}'\n"
            "cat <<'EOF'\n"
            + FAKE_FINAL
            + "EOF\n",
            encoding="utf-8",
        )
        self.runner.chmod(0o755)

    def tearDown(self):
        self.tempdir.cleanup()

    def run_make(self, review: str):
        (self.build / "peer_review.md").write_text(review, encoding="utf-8")
        final = self.build / "final.tex"
        if final.exists():
            final.unlink()
        return subprocess.run(
            [
                "make",
                f"BUILD_DIR={self.build}",
                f"IN={self.source}",
                f"LLM_RUNNER={self.runner}",
                "final",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def call_count(self) -> int:
        if not self.calls.exists():
            return 0
        return len(self.calls.read_text(encoding="utf-8").splitlines())

    def test_pass_promotes_without_any_final_model_call(self):
        result = self.run_make("STATUS: PASS\n")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.call_count(), 0)
        self.assertEqual(
            (self.build / "final.tex").read_text(encoding="utf-8"), VALID_REVISED
        )

    def test_realisation_review_runs_exactly_one_final_model_call(self):
        result = self.run_make(
            "STATUS: REVISE_REALISATION\n"
            "- [MINOR][REALISATION] Conclusion :: Remove repetition.\n"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.call_count(), 1)
        self.assertEqual(
            (self.build / "final.tex").read_text(encoding="utf-8"), FAKE_FINAL
        )

    def test_source_blocker_stops_before_final_model_call(self):
        result = self.run_make(
            "STATUS: BLOCKED_SOURCE\n"
            "- [MAJOR][SOURCE] Section 2 :: Required citation is absent from source.\n"
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.call_count(), 0)
        self.assertFalse((self.build / "final.tex").exists())
        diagnostic = (self.build / "errors" / "review.md").read_text(encoding="utf-8")
        self.assertIn("Source revision required", diagnostic)
        self.assertIn("Required citation is absent", diagnostic)


if __name__ == "__main__":
    unittest.main()
