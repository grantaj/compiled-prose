import unittest
from pathlib import Path

from tools.render_prompt import render_prompt

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class TargetLayerAuthorityTests(unittest.TestCase):
    def test_system_preserves_conceptual_emphasis_not_section_volume(self):
        system = text("prompts/00_system.md")
        self.assertNotIn(
            "Maintain proportional emphasis (no collapsing or inflating sections)",
            system,
        )
        self.assertIn("Preserve the authored hierarchy of conceptual importance", system)
        self.assertIn("may redistribute explanatory space", system)
        self.assertIn("must not add, omit, strengthen, weaken, or re-scope", system)

    def test_system_stage_awareness_describes_transformation_boundaries(self):
        system = text("prompts/00_system.md")
        for leaked_summary in (
            "Draft: literal expansion",
            "Smooth: syntactic clarity only",
            "Revise: coherence and flow only",
        ):
            with self.subTest(summary=leaked_summary):
                self.assertNotIn(leaked_summary, system)
        self.assertIn("Draft: produce the first complete target-aware prose realisation", system)
        self.assertIn("Smooth: improve local readability and connective flow", system)
        self.assertIn("Revise: improve document-level coherence and target realisation", system)

    def test_peer_review_support_defects_are_target_or_source_relative(self):
        review = text("prompts/40_peer_review.md")
        self.assertNotIn("unsupported non-trivial claim", review)
        self.assertIn(
            "support that is required by the selected target, the authoritative source's evidentiary semantics, or the claim's own evidentiary or attribution semantics",
            review,
        )
        self.assertIn(
            "Do not classify a claim as SOURCE merely because it is non-trivial or lacks scholarly citation",
            review,
        )
        self.assertIn(
            "only when the selected target, source semantics, or the claim's own evidentiary or attribution semantics establishes that support obligation",
            review,
        )

    def test_non_academic_target_composition_does_not_reintroduce_academic_support_default(self):
        rendered = render_prompt(
            system=text("prompts/00_system.md"),
            target=text("prompts/targets/magazine_general.md"),
            stage=text("prompts/40_peer_review.md"),
            source_text="# Source\n- An authored claim.",
            input_text="A rendered claim.",
            output_type="md",
        )
        self.assertIn("Scholarly citations are not required merely by this target", rendered)
        self.assertNotIn("unsupported non-trivial claim", rendered)
        self.assertIn(
            "A support defect exists only when the selected target, the authoritative source's evidentiary semantics",
            rendered,
        )


if __name__ == "__main__":
    unittest.main()
