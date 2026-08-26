import unittest
from pathlib import Path

from tools.review_decision import parse_review

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class PeerReviewCalibrationContractTests(unittest.TestCase):
    def test_nonfatal_scholarly_criticism_can_survive_pass(self):
        decision = parse_review(
            "STATUS: PASS\n"
            "- [MAJOR][ADVISORY] Scholarly positioning :: A close antecedent would "
            "improve contextualisation, but no material conflict with the claimed "
            "contribution has been established.\n"
        )
        self.assertEqual(decision.status, "PASS")
        self.assertEqual(decision.findings[0].level, "ADVISORY")

    def test_advisory_does_not_displace_required_realisation_revision(self):
        decision = parse_review(
            "STATUS: REVISE_REALISATION\n"
            "- [MAJOR][ADVISORY] Scholarly positioning :: Prior work would provide "
            "useful ancestry without changing the article's viability.\n"
            "- [MAJOR][REALISATION] Case-study discussion :: The prose overstates "
            "what one supplied case establishes.\n"
        )
        self.assertEqual(decision.status, "REVISE_REALISATION")
        self.assertEqual(
            [finding.level for finding in decision.findings],
            ["ADVISORY", "REALISATION"],
        )

    def test_genuine_external_novelty_conflict_still_blocks(self):
        decision = parse_review(
            "STATUS: BLOCKED_SOURCE\n"
            "- [MAJOR][SOURCE] Central contribution :: Prior work substantially "
            "formulates the same contribution, making the article's central "
            "originality claim materially overstated.\n"
        )
        self.assertEqual(decision.status, "BLOCKED_SOURCE")

    def test_academic_target_distinguishes_relevance_from_material_consequence(self):
        target = text("prompts/targets/journal_academic.md")
        self.assertIn("Treat relevance and material consequence separately", target)
        self.assertIn("reported as ADVISORY", target)
        self.assertIn("Escalate external prior work to SOURCE only", target)

    def test_academic_target_follows_normal_abstract_citation_convention(self):
        target = text("prompts/targets/journal_academic.md")
        self.assertIn("abstract ordinarily may summarise claims", target)
        self.assertIn("properly supported in the article body", target)


if __name__ == "__main__":
    unittest.main()
