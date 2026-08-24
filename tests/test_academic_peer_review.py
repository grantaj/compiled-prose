import tempfile
import unittest
from pathlib import Path

from tools.openai_responses import response_tool_kwargs
from tools.review_decision import SourceReviewBlocked, apply_review_decision

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class AcademicReviewToolBoundaryTests(unittest.TestCase):
    def test_academic_peer_review_requires_hosted_web_search(self):
        self.assertEqual(
            response_tool_kwargs(
                stage="prompts/40_peer_review.md",
                target="prompts/targets/journal_academic.md",
            ),
            {"tools": [{"type": "web_search"}], "tool_choice": "required"},
        )

    def test_prose_stages_never_receive_web_search(self):
        for stage in (
            "prompts/05_summarize.md",
            "prompts/10_draft.md",
            "prompts/20_smooth.md",
            "prompts/30_revise.md",
            "prompts/50_final.md",
        ):
            with self.subTest(stage=stage):
                self.assertEqual(
                    response_tool_kwargs(
                        stage=stage,
                        target="prompts/targets/journal_academic.md",
                    ),
                    {},
                )

    def test_non_academic_review_does_not_receive_web_search(self):
        for target in (
            "prompts/targets/magazine_general.md",
            "prompts/targets/explain_like_im_5.md",
        ):
            with self.subTest(target=target):
                self.assertEqual(
                    response_tool_kwargs(
                        stage="prompts/40_peer_review.md",
                        target=target,
                    ),
                    {},
                )

    def test_search_grant_is_exact_not_basename_based(self):
        self.assertEqual(
            response_tool_kwargs(
                stage="custom/40_peer_review.md",
                target="prompts/targets/journal_academic.md",
            ),
            {},
        )
        self.assertEqual(
            response_tool_kwargs(
                stage="prompts/40_peer_review.md",
                target="custom/journal_academic.md",
            ),
            {},
        )

    def test_makefile_passes_target_identity_to_provider_adapter(self):
        makefile = text("Makefile")
        self.assertIn('COMPILED_PROSE_TARGET="$(TARGET_STYLE)"', makefile)
        self.assertEqual(makefile.count("COMPILED_PROSE_TARGET="), 1)


class ExternalReviewFindingGateTests(unittest.TestCase):
    def test_external_novelty_finding_blocks_before_finalisation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review = root / "peer_review.md"
            revised = root / "revise.tex"
            final = root / "final.tex"
            review_error = root / "errors" / "review.md"
            final_error = root / "errors" / "final.md"

            review.write_text(
                "STATUS: BLOCKED_SOURCE\n"
                "- [MAJOR][SOURCE] Central contribution :: Doe (1999) appears to formulate the same mechanism, materially narrowing the claimed novelty.\n",
                encoding="utf-8",
            )
            revised.write_text(
                "\\documentclass{article}\n\\begin{document}\nClaim.\n\\end{document}\n",
                encoding="utf-8",
            )

            with self.assertRaises(SourceReviewBlocked):
                apply_review_decision(
                    review=review,
                    revised=revised,
                    final_output=final,
                    review_diagnostic=review_error,
                    final_diagnostic=final_error,
                )

            self.assertFalse(final.exists())
            diagnostic = review_error.read_text(encoding="utf-8")
            self.assertIn("Source revision required", diagnostic)
            self.assertIn("Doe (1999)", diagnostic)


if __name__ == "__main__":
    unittest.main()
