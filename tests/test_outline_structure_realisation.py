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
        self.assertIn("genuine procedures", review)
        self.assertIn("taxonomy membership", review)
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

    def test_peer_review_checks_structural_realisation_without_banning_lists(self):
        review = text("prompts/40_peer_review.md")
        self.assertIn("mechanical projection of source presentation topology", review)
        self.assertIn("One-source-item → one-target-unit mapping", review)
        self.assertIn("signals to inspect, not violations themselves", review)
        self.assertIn("Do not penalise explicit structure merely for being explicit", review)
        self.assertIn("numbered procedure can be the correct target form", review)
        self.assertIn("Assess development and integration, not only sentence polish", review)

    def test_journal_exhaustive_coverage_is_semantic_not_checklist_visible(self):
        journal = text("prompts/targets/journal_academic.md")
        self.assertIn("Coverage is exhaustive for this target.", journal)
        self.assertIn(
            "Exhaustive conceptual coverage is not a requirement to visibly discharge source items one by one",
            journal,
        )
        self.assertIn("rhetorical reorganisation are permitted and expected", journal)
        self.assertIn("not as a one-to-one projection of source headings", journal)
        self.assertIn("Lists, tables, taxonomies, classifications, and numbered procedures", journal)
        self.assertIn("Do not inherit them merely because the source used bullets or enumeration", journal)
        self.assertIn("rather than mechanically replaying the source's terminal bullets", journal)

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
        self.assertIn("mechanical projection of source presentation topology", pipeline)
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
        self.assertIn("checklist-style progression", journal)
        self.assertIn("numbered procedures are appropriate", journal)

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
