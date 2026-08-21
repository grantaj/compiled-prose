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

    def test_system_makes_target_authoritative_for_core_realisation_dimensions(self):
        system = text("prompts/00_system.md")
        self.assertIn(
            "Within the core target-driven publication stages (draft, smooth, revise, peer review, and final)",
            system,
        )
        self.assertIn("the selected target is authoritative", system)
        for dimension in (
            "audience",
            "venue",
            "tone",
            "register",
            "reading level",
            "rhetorical form",
            "paragraph/section granularity",
            "citation presentation",
        ):
            with self.subTest(dimension=dimension):
                self.assertIn(dimension, system)
        self.assertIn(
            "Generic stage instructions may define permitted transformations but must not impose conflicting defaults",
            system,
        )
        self.assertIn(
            "An auxiliary transform may define an intrinsic artefact shape as part of its stage responsibility",
            system,
        )
        self.assertIn(
            "that shape is not a publication-style default for the core pipeline",
            system,
        )

    def test_system_defines_source_assurance_floor_and_target_rigour_overlay(self):
        system = text("prompts/00_system.md")
        self.assertIn("Source assurance has a target-independent floor", system)
        self.assertIn("may impose additional explicit rigour above that floor", system)
        self.assertIn("cannot make an internally contradictory", system)
        self.assertIn("less formal presentation", system)
        self.assertIn(
            "Target-specific review must not import academic or otherwise stricter conventions",
            system,
        )

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
        self.assertIn("Peer review: perform source assurance, then diagnose target-relative", system)

    def test_explicit_target_structural_choice_is_not_overridden_by_draft_defaults(self):
        target = """# Synthetic target
Use frequent short sections and LaTeX lists when they improve this target's readability.
Do not change authored concepts, grouping, order, or scope to create them.
"""
        rendered = render_prompt(
            system=text("prompts/00_system.md"),
            target=target,
            stage=text("prompts/10_draft.md"),
            source_text="# Source\n- First authored step.\n- Second authored step.",
            input_text="# Source\n- First authored step.\n- Second authored step.",
            output_type="tex",
        )
        self.assertIn("Use frequent short sections and LaTeX lists", rendered)
        self.assertIn("the selected target is authoritative", rendered)
        self.assertNotIn("Avoid list formatting by default", rendered)
        self.assertNotIn("Prefer a small number of coherent publication sections", rendered)
        self.assertNotIn("Only emit LaTeX lists when the authoritative source explicitly specifies list structure", rendered)

    def test_peer_review_uses_source_assurance_floor_then_target_calibrated_overlay(self):
        review = text("prompts/40_peer_review.md")
        self.assertNotIn("unsupported non-trivial claim", review)
        self.assertIn("Source assurance has a target-independent floor", review)
        self.assertIn("Perform the review in this order", review)
        self.assertIn("1. Source assurance", review)
        self.assertIn("2. Target realisation assurance", review)
        self.assertIn("may impose additional explicitness, rigour, evidence, or citation requirements", review)
        self.assertIn("may not lower the source-assurance floor", review)
        self.assertIn(
            "Do not import academic or otherwise stricter venue conventions",
            review,
        )
        self.assertIn(
            "Do not classify a claim as SOURCE merely because it is non-trivial or lacks scholarly citation",
            review,
        )

    def test_non_academic_target_composition_keeps_support_floor_without_academic_leakage(self):
        rendered = render_prompt(
            system=text("prompts/00_system.md"),
            target=text("prompts/targets/magazine_general.md"),
            stage=text("prompts/40_peer_review.md"),
            source_text="# Source\n- An authored claim.",
            input_text="A rendered claim.",
            output_type="md",
        )
        self.assertIn("Scholarly citations are not required merely by this target", rendered)
        self.assertIn("Source assurance has a target-independent floor", rendered)
        self.assertIn("Ask first whether the claim and argument satisfy the target-independent", rendered)
        self.assertIn("do not convert adequate support into an academic-style explanation burden", rendered)
        self.assertNotIn("unsupported non-trivial claim", rendered)

    def test_pipeline_requires_empirical_justification_for_new_model_stages(self):
        pipeline = text("pipeline.md")
        self.assertIn("Each model-backed stage incurs user-visible execution cost", pipeline)
        self.assertIn("Architectural separation alone is not sufficient justification", pipeline)
        self.assertIn("empirical evidence", pipeline)
        self.assertIn("an existing stage cannot absorb the responsibility reliably", pipeline)

        makefile = text("Makefile")
        self.assertEqual(makefile.count("$(call RUN_STAGE,"), 6)
        for stage in ("draft", "smooth", "revise", "review", "final", "summarize"):
            with self.subTest(stage=stage):
                self.assertEqual(makefile.count(f"$(call RUN_STAGE,{stage},"), 1)


if __name__ == "__main__":
    unittest.main()
