import unittest
from pathlib import Path

from tools.render_prompt import render_prompt

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class TargetLayerAuthorityTests(unittest.TestCase):
    def test_system_makes_coverage_target_owned_without_changing_source_meaning(self):
        system = text("prompts/00_system.md")
        self.assertNotIn(
            "Maintain proportional emphasis (no collapsing or inflating sections)",
            system,
        )
        self.assertIn("Coverage and compression are realisation responsibilities", system)
        self.assertIn("the default is exhaustive conceptual coverage", system)
        self.assertIn(
            "A target may explicitly authorise summarisation, compression, or selective omission.",
            system,
        )
        self.assertIn(
            "Presentation reorganisation is a baseline realisation freedom, not a coverage reduction",
            system,
        )
        self.assertNotIn(
            "summarisation, compression, selective omission, or presentation reordering",
            system,
        )
        self.assertIn(
            "does not change the authoritative source or grant permission to alter the conceptual scope or meaning of retained material",
            system,
        )

    def test_system_makes_target_authoritative_for_core_realisation_dimensions(self):
        system = text("prompts/00_system.md")
        self.assertIn(
            "Within the core target-driven realisation stages (draft, smooth, revise, peer review, and final)",
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
            "coverage and compression",
            "paragraph/section granularity",
            "evidence/attribution/citation presentation",
        ):
            with self.subTest(dimension=dimension):
                self.assertIn(dimension, system)
        self.assertIn(
            "must not impose conflicting academic, citation, rhetorical, or other venue defaults",
            system,
        )
        self.assertIn(
            "An auxiliary transform may define an intrinsic artefact shape or coverage as part of its stage responsibility",
            system,
        )
        self.assertIn(
            "that is not a target-style default for the core pipeline",
            system,
        )

    def test_system_defines_source_assurance_floor_without_academic_presentation_leakage(self):
        system = text("prompts/00_system.md")
        self.assertIn("Source assurance has a target-independent floor", system)
        self.assertIn("may impose additional explicit rigour above that floor", system)
        self.assertIn("cannot make an internally contradictory", system)
        self.assertIn("less formal or more selective presentation", system)
        self.assertIn(
            "does **not** impose scholarly citation apparatus, academic prose conventions, or academic-style visible reasoning",
            system,
        )
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
        self.assertIn("Draft: produce the first complete target-aware text realisation", system)
        self.assertIn("Smooth: improve local readability and connective flow", system)
        self.assertIn("Revise: improve document-level coherence and target realisation", system)
        self.assertIn("Peer review: independently assess compilation integrity and writing quality", system)

    def test_generic_chain_does_not_impose_adult_publication_shape(self):
        generic = "\n".join(
            text(path)
            for path in (
                "prompts/00_system.md",
                "prompts/10_draft.md",
                "prompts/20_smooth.md",
                "prompts/30_revise.md",
                "prompts/40_peer_review.md",
                "prompts/50_final.md",
            )
        )
        for leaked_prior in (
            "publication-quality prose",
            "first-draft expansion",
            "connected prose according to",
            "one-to-one publication section map",
            "publication sections",
            "generic publication shape",
            "publication-quality revision",
            "Assess argument thread",
            "publication sectioning serves",
            "publication-ready LaTeX text",
        ):
            with self.subTest(leaked_prior=leaked_prior):
                self.assertNotIn(leaked_prior, generic)
        self.assertIn(
            "do not infer rhetorical form, sectioning, tone, or document genre from the fact that the output format is LaTeX",
            text("prompts/10_draft.md"),
        )
        self.assertIn(
            "Do not import academic, adult-publication, argumentative, or otherwise stricter conventions",
            text("prompts/40_peer_review.md"),
        )

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

    def test_peer_review_separates_source_integrity_from_target_writing_quality(self):
        review = text("prompts/40_peer_review.md")
        self.assertNotIn("unsupported non-trivial claim", review)
        self.assertIn("target-independent source-assurance floor", review)
        self.assertIn("two independent axes", review)
        self.assertIn("1. Compilation integrity", review)
        self.assertIn("2. Target writing quality", review)
        self.assertIn("Fidelity is not evidence of writing quality", review)
        self.assertIn("Apply target-specific coverage, rigour, evidence, attribution, and citation requirements", review)
        self.assertIn(
            "Do not import academic, adult-publication, argumentative, or otherwise stricter conventions",
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
        self.assertIn("target-independent source-assurance floor", rendered)
        self.assertIn("Formal scholarly citation apparatus is not globally required", rendered)
        self.assertIn("Do not import academic, adult-publication, argumentative, or otherwise stricter conventions", rendered)
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
