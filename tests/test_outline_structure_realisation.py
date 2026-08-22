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
        self.assertIn("Do not create a section or subsection merely because", draft)
        self.assertIn("according to the selected target", draft)
        self.assertNotIn("Prefer a small number of coherent publication sections", draft)
        self.assertNotIn(
            "render them as the corresponding level of LaTeX sectioning commands",
            draft,
        )

    def test_draft_list_and_item_realisation_is_target_relative(self):
        draft = text("prompts/10_draft.md")
        self.assertNotIn("Avoid list formatting by default", draft)
        self.assertNotIn(
            "Only emit LaTeX lists when the authoritative source explicitly specifies list structure",
            draft,
        )
        self.assertIn("Do not mechanically preserve or suppress list formatting", draft)
        self.assertIn(
            "Do not require one source item to map to one sentence, paragraph, list item, or section",
            draft,
        )

    def test_downstream_stages_can_repair_sectioning_within_target_permissions(self):
        smooth = text("prompts/20_smooth.md")
        revise = text("prompts/30_revise.md")
        review = text("prompts/40_peer_review.md")
        final = text("prompts/50_final.md")

        for stage in (smooth, revise, final):
            with self.subTest(stage=stage[:40]):
                self.assertIn("realisation choices", stage)
                self.assertIn("Consolidate, reorder, or omit", stage)
                self.assertIn("selected target", stage)
                self.assertIn("generic publication shape", stage)

        self.assertIn("publication sectioning serves the selected target", review)
        self.assertIn("sectioning and ordering as realisation choices", review)
        self.assertIn("not as authority to alter conceptual relationships", review)

    def test_structural_order_defaults_to_source_but_target_may_explicitly_reorder(self):
        draft = text("prompts/10_draft.md")
        smooth = text("prompts/20_smooth.md")
        revise = text("prompts/30_revise.md")
        final = text("prompts/50_final.md")

        self.assertIn(
            "Preserve authored order unless the selected target explicitly permits presentation reordering",
            draft,
        )
        self.assertIn("logical dependencies among retained ideas", draft)
        for stage in (smooth, revise, final):
            with self.subTest(stage=stage[:40]):
                self.assertIn("Preserve authored order by default", stage)
                self.assertIn("presentation reordering", stage)
                self.assertIn("logical dependencies among retained ideas", stage)


if __name__ == "__main__":
    unittest.main()
