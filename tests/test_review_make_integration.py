import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REALISE = (
    "\\documentclass{article}\n"
    "\\begin{document}\n"
    "Realised authored prose.\n"
    "\\end{document}\n"
)
FINAL = (
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
        self.source = self.root / "source.md"
        self.source.write_text("# Source\n- Authored claim\n", encoding="utf-8")
        self.review_file = self.root / "review.txt"
        self.calls = self.root / "runner-calls.txt"
        self.runner = self.root / "fake-runner.sh"
        self.runner.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "cat >/dev/null\n"
            f"printf '%s\\n' \"$COMPILED_PROSE_STAGE\" >> '{self.calls}'\n"
            "case \"$COMPILED_PROSE_STAGE\" in\n"
            "  prompts/10_realise.md) cat <<'DOC'\n"
            + REALISE
            + "DOC\n    ;;\n"
            f"  prompts/40_peer_review.md) cat '{self.review_file}' ;;\n"
            "  prompts/50_final.md) cat <<'DOC'\n"
            + FINAL
            + "DOC\n    ;;\n"
            "  *) echo unexpected-stage >&2; exit 9 ;;\n"
            "esac\n",
            encoding="utf-8",
        )
        self.runner.chmod(0o755)

    def tearDown(self):
        self.tempdir.cleanup()

    def run_make(self, review: str):
        self.review_file.write_text(review, encoding="utf-8")
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

    def stages(self):
        if not self.calls.exists():
            return []
        return self.calls.read_text(encoding="utf-8").splitlines()

    def test_pass_promotes_realisation_without_post_review_model_call(self):
        result = self.run_make("STATUS: PASS\n")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.stages(),
            ["prompts/10_realise.md", "prompts/40_peer_review.md"],
        )
        self.assertEqual(
            (self.build / "final.tex").read_text(encoding="utf-8"), REALISE
        )

    def test_realisation_review_runs_exactly_one_final_model_call(self):
        result = self.run_make(
            "STATUS: REVISE_REALISATION\n"
            "- [MINOR][REALISATION] Conclusion :: Remove repetition.\n"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.stages(),
            [
                "prompts/10_realise.md",
                "prompts/40_peer_review.md",
                "prompts/50_final.md",
            ],
        )
        self.assertEqual(
            (self.build / "final.tex").read_text(encoding="utf-8"), FINAL
        )

    def test_source_blocker_stops_before_final_revision(self):
        result = self.run_make(
            "STATUS: BLOCKED_SOURCE\n"
            "- [MAJOR][SOURCE] Section 2 :: Required citation is absent from source.\n"
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(
            self.stages(),
            ["prompts/10_realise.md", "prompts/40_peer_review.md"],
        )
        self.assertFalse((self.build / "final.tex").exists())
        diagnostic = (self.build / "errors" / "review.md").read_text(encoding="utf-8")
        self.assertIn("Source revision required", diagnostic)
        self.assertIn("Required citation is absent", diagnostic)


if __name__ == "__main__":
    unittest.main()
