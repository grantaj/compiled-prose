import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class OutlineStructureRealisationTests(unittest.TestCase):
    def test_draft_does_not_map_outline_headings_one_to_one_to_latex_sections(self):
        draft = text("prompts/10_draft.md")
        self.assertIn("not as a one-to-one publication section map", draft)
        self.assertIn("Do not copy outline navigation numbering or labels", draft)
        self.assertIn("Prefer a small number of coherent publication sections", draft)
        self.assertIn("do not create a section or subsection merely because", draft)
        self.assertNotIn(
            "render them as the corresponding level of LaTeX sectioning commands",
            draft,
        )

    def test_downstream_stages_can_repair_over_sectioning_without_claiming_authority(self):
        smooth = text("prompts/20_smooth.md")
        revise = text("prompts/30_revise.md")
        review = text("prompts/40_peer_review.md")
        final = text("prompts/50_final.md")

        for stage in (smooth, revise, final):
            with self.subTest(stage=stage[:40]):
                self.assertIn("realisation choices", stage)
                self.assertIn("duplicated manual numbering", stage)

        self.assertIn("mechanically mirroring the outline", review)
        self.assertIn("gratuitous one-heading-per-outline-item", review)
        self.assertIn("duplicated manual-plus-LaTeX section numbering", review)
        self.assertIn("REALISATION defects", review)

    def test_structural_realisation_still_preserves_authored_order_and_distinctions(self):
        draft = text("prompts/10_draft.md")
        smooth = text("prompts/20_smooth.md")
        revise = text("prompts/30_revise.md")
        final = text("prompts/50_final.md")

        self.assertIn("Preserve the order and distinctions they express", draft)
        for stage in (smooth, revise, final):
            with self.subTest(stage=stage[:40]):
                self.assertIn("authored order", stage)
                self.assertIn("scope", stage)


if __name__ == "__main__":
    unittest.main()
