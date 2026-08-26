import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.review_decision import (
    ReviewProtocolError,
    SourceReviewBlocked,
    apply_review_decision,
    parse_review,
)

ROOT = Path(__file__).resolve().parents[1]


class ReviewProtocolTests(unittest.TestCase):
    def test_pass_requires_no_findings(self):
        decision = parse_review("STATUS: PASS\n")
        self.assertEqual(decision.status, "PASS")
        self.assertEqual(decision.findings, [])

    def test_realisation_findings_require_bounded_revision_status(self):
        decision = parse_review(
            "STATUS: REVISE_REALISATION\n"
            "- [MINOR][REALISATION] Section 2, paragraph 3 :: Transition is abrupt.\n"
        )
        self.assertEqual(decision.status, "REVISE_REALISATION")
        self.assertEqual(decision.findings[0].level, "REALISATION")

    def test_any_source_finding_requires_blocked_status(self):
        decision = parse_review(
            "STATUS: BLOCKED_SOURCE\n"
            "- [MINOR][REALISATION] Section 1 :: Sentence is repetitive.\n"
            "- [MAJOR][SOURCE] Section 3 :: Claim lacks an authored warrant.\n"
        )
        self.assertEqual(decision.status, "BLOCKED_SOURCE")

    def test_malformed_or_inconsistent_status_fails_instead_of_guessing(self):
        invalid_reports = (
            "",
            "STATUS: MAYBE\n",
            "STATUS: PASS\nSTATUS: PASS\n",
            "- [MINOR][REALISATION] Section 1 :: Awkward.\nSTATUS: REVISE_REALISATION\n",
            "STATUS: PASS\n- [MINOR][REALISATION] Section 1 :: Awkward.\n",
            "STATUS: REVISE_REALISATION\n",
            "STATUS: REVISE_REALISATION\n- [MINOR][SOURCE] Section 1 :: Missing evidence.\n",
            "STATUS: REVISE_REALISATION\n1. MINOR: Awkward.\n",
        )
        for report in invalid_reports:
            with self.subTest(report=report):
                with self.assertRaises(ReviewProtocolError):
                    parse_review(report)


class ReviewDecisionTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.review = self.root / "peer_review.md"
        self.realised = self.root / "realise.tex"
        self.final = self.root / "final.tex"
        self.review_error = self.root / "errors" / "review.md"
        self.final_error = self.root / "errors" / "final.md"
        self.realised.write_text(
            "\\documentclass{article}\n\\begin{document}\nAuthored prose.\n\\end{document}\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def apply(self):
        return apply_review_decision(
            review=self.review,
            realised=self.realised,
            final_output=self.final,
            review_diagnostic=self.review_error,
            final_diagnostic=self.final_error,
        )

    def test_pass_promotes_realised_artifact_without_model_revision(self):
        expected = (
            b"\\documentclass{article}\r\n"
            b"\\begin{document}\r\n"
            b"Authored prose.\r\n"
            b"\\end{document}\r\n"
        )
        self.realised.write_bytes(expected)
        self.review.write_text("STATUS: PASS\n", encoding="utf-8")
        self.review_error.parent.mkdir(parents=True)
        self.review_error.write_text("stale review error", encoding="utf-8")
        self.final_error.write_text("stale final error", encoding="utf-8")

        decision = self.apply()

        self.assertEqual(decision.status, "PASS")
        self.assertEqual(self.final.read_bytes(), expected)
        self.assertFalse(self.review_error.exists())
        self.assertFalse(self.final_error.exists())

    def test_realisation_review_removes_stale_final_and_allows_one_later_pass(self):
        self.review.write_text(
            "STATUS: REVISE_REALISATION\n"
            "- [MINOR][REALISATION] Conclusion :: Repeats the preceding sentence.\n",
            encoding="utf-8",
        )
        self.final.write_text("stale final", encoding="utf-8")
        self.final_error.parent.mkdir(parents=True)
        self.final_error.write_text("stale final error", encoding="utf-8")

        decision = self.apply()

        self.assertEqual(decision.status, "REVISE_REALISATION")
        self.assertFalse(self.final.exists())
        self.assertFalse(self.final_error.exists())

    def test_unprovided_citation_is_source_blocker_and_never_becomes_final(self):
        self.review.write_text(
            "STATUS: BLOCKED_SOURCE\n"
            "- [MAJOR][SOURCE] Section 4, claim on prevalence :: Target requires a citation not supplied by the authoritative source.\n",
            encoding="utf-8",
        )
        self.final.write_text("nominal stale final", encoding="utf-8")
        self.final_error.parent.mkdir(parents=True)
        self.final_error.write_text("stale final error", encoding="utf-8")

        with self.assertRaises(SourceReviewBlocked):
            self.apply()

        self.assertFalse(self.final.exists())
        self.assertFalse(self.final_error.exists())
        diagnostic = self.review_error.read_text(encoding="utf-8")
        self.assertIn("Source revision required", diagnostic)
        self.assertIn("citation not supplied", diagnostic)

    def test_source_blocker_cli_exits_nonzero(self):
        self.review.write_text(
            "STATUS: BLOCKED_SOURCE\n"
            "- [MAJOR][SOURCE] Introduction :: Scope boundary is missing.\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "review_decision.py"),
                "--review",
                str(self.review),
                "--realised",
                str(self.realised),
                "--output",
                str(self.final),
                "--diagnostic",
                str(self.review_error),
                "--final-diagnostic",
                str(self.final_error),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.final.exists())
        self.assertTrue(self.review_error.exists())

    def test_malformed_review_cli_fails_clearly_and_removes_stale_final(self):
        self.review.write_text("REVIEW AGAIN: YES\n", encoding="utf-8")
        self.final.write_text("stale final", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "review_decision.py"),
                "--review",
                str(self.review),
                "--realised",
                str(self.realised),
                "--output",
                str(self.final),
                "--diagnostic",
                str(self.review_error),
                "--final-diagnostic",
                str(self.final_error),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.final.exists())
        self.assertIn("Review protocol error", self.review_error.read_text(encoding="utf-8"))
        self.assertIn("diagnostics:", result.stderr)


class BoundedOrchestrationTests(unittest.TestCase):
    def test_makefile_has_exactly_one_final_model_stage_and_no_recursive_loop(self):
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertEqual(makefile.count("$(call RUN_STAGE,final,"), 1)
        final_start = makefile.index("$(FINAL_OUT):")
        final_end = makefile.index("\n$(SUMMARY_OUT):", final_start)
        final_block = makefile[final_start:final_end]
        self.assertNotIn("$(MAKE)", final_block)
        self.assertIn("python tools/review_decision.py", final_block)
        self.assertIn("REVISE_REALISATION)", final_block)
        self.assertIn("PASS)", final_block)

    def test_peer_review_prompt_declares_machine_status_vocabulary(self):
        prompt = (ROOT / "prompts" / "40_peer_review.md").read_text(encoding="utf-8")
        self.assertIn("STATUS: PASS", prompt)
        self.assertIn("STATUS: REVISE_REALISATION", prompt)
        self.assertIn("STATUS: BLOCKED_SOURCE", prompt)
        self.assertNotIn('"REVIEW AGAIN: YES"', prompt)


if __name__ == "__main__":
    unittest.main()
