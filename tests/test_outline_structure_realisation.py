import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class OutlineStructureRealisationTests(unittest.TestCase):
    def test_system_separates_conceptual_from_presentation_topology(self):
        system = text("prompts/00_system.md")
        self.assertIn("Conceptual topology is authoritative", system)
        self.assertIn("source presentation topology is not authoritative by default", system)
        for relationship in (
            "logical dependencies",
            "qualification and uncertainty scope",
            "taxonomy membership",
            "procedures, chronology, priority, or sequence",
            "evidentiary, attribution, and citation relationships",
        ):
            with self.subTest(relationship=relationship):
                self.assertIn(relationship, system)
        for presentation_feature in (
            "bullets",
            "numbering",
            "heading depth",
            "fragment boundaries",
            "adjacency",
            "source navigation order",
        ):
            with self.subTest(presentation_feature=presentation_feature):
                self.assertIn(presentation_feature, system)

    def test_rhetorical_reorganisation_no_longer_requires_target_permission(self):
        system = text("prompts/00_system.md")
        draft = text("prompts/10_draft.md")
        smooth = text("prompts/20_smooth.md")
        revise = text("prompts/30_revise.md")
        final = text("prompts/50_final.md")

        self.assertIn(
            "without requiring an explicit target permission to reorganise presentation",
            system,
        )
        self.assertIn(
            "Presentation reorganisation is a baseline realisation freedom, not a coverage reduction",
            system,
        )
        self.assertNotIn(
            "Preserve authored order unless the selected target explicitly permits presentation reordering",
            draft,
        )
        for stage in (smooth, revise, final):
            with self.subTest(stage=stage[:40]):
                self.assertNotIn("Preserve authored order by default", stage)
                self.assertIn("conceptual topology", stage.lower())

    def test_genuine_ordered_and_grouped_structures_remain_authoritative(self):
        system = text("prompts/00_system.md")
        draft = text("prompts/10_draft.md")
        review = text("prompts/40_peer_review.md")
        final = text("prompts/50_final.md")

        self.assertIn("When an authored ordering is semantically meaningful", system)
        self.assertIn("procedure, dependency chain, chronology, priority", system)
        self.assertIn("Preserve explicit list, table, taxonomy, or numbered form", draft)
        self.assertIn("conceptual topology and provenance are preserved", review)
        self.assertIn("altered dependencies or qualifications", review)
        self.assertIn("turn an ordered procedure into unordered prose", final)

    def test_draft_does_not_map_outline_items_or_headings_one_to_one(self):
        draft = text("prompts/10_draft.md")
        self.assertIn("not as a one-to-one target-output structure map", draft)
        self.assertIn("Do not copy outline navigation numbering or labels", draft)
        self.assertIn("Do not create a section or subsection merely because", draft)
        self.assertIn(
            "Do not require one source item to map to one sentence, paragraph, list item, section, or other target-facing unit",
            draft,
        )
        self.assertIn("A source list may become integrated prose", draft)
        self.assertNotIn("Avoid list formatting by default", draft)

    def test_peer_review_judges_target_quality_before_source_classification(self):
        review = text("prompts/40_peer_review.md")
        self.assertIn("Review order is mandatory", review)
        self.assertIn("1. Independent target review", review)
        self.assertIn("2. Source comparison and defect classification", review)
        self.assertIn("3. Compilation integrity", review)
        self.assertIn("submitted directly as a finished work of the selected target", review)
        self.assertIn("Exercise ordinary editorial judgement", review)
        self.assertIn("Do not reduce this judgement to a checklist of surface forms", review)
        self.assertIn("Lists, headings, short sections, serial exposition", review)
        self.assertIn(
            "Source comparison determines where the defect belongs, not whether the defect exists",
            review,
        )
        self.assertIn("Fidelity alone can never justify PASS", review)
        self.assertIn("would require no material revision", review)

    def test_journal_preserves_complete_argument_without_source_item_inventory(self):
        journal = text("prompts/targets/journal_academic.md")
        self.assertIn("Preserve the complete authored argument, not an inventory of source fragments", journal)
        self.assertNotIn("Coverage is exhaustive for this target.", journal)
        self.assertIn("synthesised, compressed, subordinated, consolidated, split, or reorganised", journal)
        self.assertIn("should read as an article conceived for this venue", journal)
        self.assertIn("normal standards of good peer-reviewed academic writing", journal)
        self.assertIn("Source bullets, numbering, heading depth", journal)
        self.assertIn("Use lists, tables, classifications, numbered procedures", journal)

    def test_pipeline_spec_records_the_same_topology_boundary(self):
        pipeline = text("pipeline.md")
        self.assertIn(
            "Conceptual topology and presentation topology are deliberately separate",
            pipeline,
        )
        self.assertIn(
            "without a special target permission when that changes only presentation topology",
            pipeline,
        )
        self.assertIn("Target writing quality", pipeline)
        self.assertNotIn("target-owned coverage, ordering permissions", pipeline)

    def test_censorship_shape_exercises_both_presentation_and_conceptual_structure(self):
        source = text("tests/fixtures/censorship_topology_excerpt.md")
        # Authoring-convenience structures that should not force target-facing units.
        self.assertIn("## Contribution", source)
        self.assertIn("## Boundary factors", source)
        self.assertIn("## Stress tests", source)
        self.assertIn("## Conclusion", source)
        # Semantically structured material whose relationships must survive.
        self.assertIn("## Operational families", source)
        self.assertIn("### Exclusion", source)
        self.assertIn("### Attenuation", source)
        self.assertIn("## Classification sequence", source)
        self.assertIn("8. Move only then", source)

        system = text("prompts/00_system.md")
        journal = text("prompts/targets/journal_academic.md")
        self.assertIn("taxonomy membership", system)
        self.assertIn("procedure", system)
        self.assertIn("numbered procedures", journal)
        self.assertIn("genuine logical and conceptual structure", journal)

    def test_reorganisation_cannot_invent_connective_reasoning_or_detach_support(self):
        for path in (
            "prompts/00_system.md",
            "prompts/10_draft.md",
            "prompts/20_smooth.md",
            "prompts/30_revise.md",
            "prompts/50_final.md",
        ):
            prompt = text(path).lower()
            with self.subTest(path=path):
                self.assertIn("connective", prompt)
                self.assertIn("warrant", prompt)
                self.assertIn("conceptual", prompt)
        system = text("prompts/00_system.md")
        self.assertIn(
            "keep qualifications, uncertainty, evidence, attribution, and citations attached",
            system,
        )


if __name__ == "__main__":
    unittest.main()
