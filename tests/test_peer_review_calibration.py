import unittest
from pathlib import Path

from tools.review_decision import parse_review

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class PeerReviewCalibrationContractTests(unittest.TestCase):
    def test_source_block_is_reserved_for_intellectual_viability(self):
        prompt = text("prompts/40_peer_review.md")
        self.assertIn("cannot responsibly make its central claims", prompt)
        self.assertIn("underlying intellectual position", prompt)
        self.assertIn("defensive machinery", prompt)

    def test_academic_review_does_not_require_proof_like_completeness(self):
        target = text("prompts/targets/journal_academic.md")
        for concept in (
            "not as mathematical proofs or formal specifications",
            "deductive closure",
            "exhaustive case coverage",
            "symmetrical cases",
        ):
            with self.subTest(concept=concept):
                self.assertIn(concept, target)

    def test_conceptual_criticism_can_continue_to_final_revision(self):
        decision = parse_review(
            "STATUS: REVISE_REALISATION\n"
            "- [MAJOR][REALISATION] Case-study discussion :: Clarify that the cases "
            "play deliberately asymmetric evidentiary roles and avoid overstating "
            "what any one case establishes.\n"
        )
        self.assertEqual(decision.status, "REVISE_REALISATION")
        self.assertEqual(decision.findings[0].level, "REALISATION")

    def test_genuine_source_defect_still_blocks(self):
        decision = parse_review(
            "STATUS: BLOCKED_SOURCE\n"
            "- [MAJOR][SOURCE] Central argument :: The conclusion depends on a premise "
            "the authoritative source never supplies.\n"
        )
        self.assertEqual(decision.status, "BLOCKED_SOURCE")


if __name__ == "__main__":
    unittest.main()
