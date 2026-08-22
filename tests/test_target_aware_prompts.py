import unittest
from pathlib import Path

from tools.render_prompt import render_prompt

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class TargetAwarePromptTests(unittest.TestCase):
    def render(
        self,
        stage: str,
        target: str,
        *,
        source="# Authoritative source\n- one authored claim",
        stage_input=None,
        review=None,
    ) -> str:
        output_type = "md" if stage.endswith("40_peer_review.md") else "tex"
        if stage_input is None:
            stage_input = source
        return render_prompt(
            system=text("prompts/00_system.md"),
            stage=text(stage),
            target=text(target),
            source_text=source,
            input_text=stage_input,
            review=review,
            output_type=output_type,
        )

    def test_rendered_authority_order_is_stable_and_stage_input_is_separate(self):
        source = "# Original authored outline\n- SOURCE_ONLY_SENTINEL"
        stage_input = (
            "\\documentclass{article}\n"
            "\\begin{document}DERIVED_ONLY_SENTINEL\\end{document}"
        )
        rendered = self.render(
            "prompts/50_final.md",
            "prompts/targets/journal_academic.md",
            source=source,
            stage_input=stage_input,
            review=(
                "STATUS: REVISE_REALISATION\n"
                "- [MINOR][REALISATION] Test paragraph :: Diagnostic only."
            ),
        )
        positions = [
            rendered.index("# Stage\n"),
            rendered.index("# Target\n"),
            rendered.index("# Authoritative Source\n"),
            rendered.index("# Stage Input (Derived Working Artefact; Non-Authoritative)\n"),
            rendered.index("# Peer Review (Markdown, Diagnostic Only)\n"),
            rendered.index("# Output Contract\n"),
        ]
        self.assertEqual(positions, sorted(positions))
        self.assertIn(source, rendered)
        self.assertIn(stage_input, rendered)
        self.assertNotIn("# Input (Markdown)", rendered)

        system = text("prompts/00_system.md")
        expected_order = (
            "1. System instructions (this file)",
            "2. Stage-specific prompt",
            "3. Target requirements",
            "4. Authoritative source",
            "5. Diagnostic context",
        )
        cursor = -1
        for item in expected_order:
            position = system.index(item)
            self.assertGreater(position, cursor)
            cursor = position

    def test_derived_stage_input_never_becomes_conceptual_authority(self):
        system = text("prompts/00_system.md")
        pipeline = text("pipeline.md")
        self.assertIn("derived working artefact", system.lower())
        self.assertIn("not a conceptual-authority layer", system)
        self.assertIn(
            "If the stage input and authoritative source conflict, the authoritative source wins.",
            system,
        )
        self.assertIn(
            "The sole source of conceptual authorship throughout the pipeline.", pipeline
        )
        self.assertIn(
            "Are inputs to later transformations but are not conceptual authority.", pipeline
        )
        self.assertNotIn("or the prior stage artefact", pipeline)

    def test_matching_source_and_stage_input_are_not_duplicated(self):
        source = "# Same source and working input\n- authored claim"
        rendered = self.render(
            "prompts/10_draft.md",
            "prompts/targets/magazine_general.md",
            source=source,
            stage_input=source,
        )
        self.assertEqual(rendered.count(source), 1)
        self.assertNotIn(
            "# Stage Input (Derived Working Artefact; Non-Authoritative)", rendered
        )

    def test_makefile_carries_original_source_alongside_every_stage_input(self):
        makefile = text("Makefile")
        self.assertIn("--source $(IN) --in $(2)", makefile)
        self.assertNotIn("--source $(2)", makefile)
        for call in (
            "$(call RUN_STAGE,draft,$(P_DRAFT),$(DRAFT_IN),tex,$@)",
            "$(call RUN_STAGE,smooth,$(P_SMOOTH),$(DRAFT_OUT),tex,$@)",
            "$(call RUN_STAGE,revise,$(P_REVISE),$(SMOOTH_OUT),tex,$@)",
            "$(call RUN_STAGE,review,$(P_REVIEW),$(REVISE_OUT),md,$@)",
            "$(call RUN_STAGE,final,$(P_FINAL),$(REVISE_OUT),tex,$@,--review $(REVIEW_OUT))",
        ):
            self.assertIn(call, makefile)

    def test_downstream_prompts_explicitly_check_stage_input_against_source(self):
        for stage in (
            "prompts/20_smooth.md",
            "prompts/30_revise.md",
            "prompts/40_peer_review.md",
            "prompts/50_final.md",
        ):
            prompt = text(stage).lower()
            with self.subTest(stage=stage):
                self.assertIn("stage input", prompt)
                self.assertIn("authoritative source", prompt)
                self.assertIn("derived", prompt)

    def test_academic_review_includes_strict_academic_citation_expectations(self):
        rendered = self.render(
            "prompts/40_peer_review.md",
            "prompts/targets/journal_academic.md",
            stage_input="\\documentclass{article}\n\\begin{document}claim\\end{document}",
        )
        self.assertIn(
            "Scholarly citation support is required for claims that depend on external literature",
            rendered,
        )
        self.assertIn(
            "Apply scholarly citation expectations only when the selected target requires them.",
            rendered,
        )
        self.assertIn(
            "If target-required citation or evidence support is absent",
            rendered,
        )

    def test_non_academic_review_does_not_inherit_academic_reference_obligations(self):
        rendered = self.render(
            "prompts/40_peer_review.md",
            "prompts/targets/magazine_general.md",
            stage_input="\\documentclass{article}\n\\begin{document}claim\\end{document}",
        )
        self.assertIn(
            "Scholarly citations are not required merely by this target.", rendered
        )
        self.assertIn(
            "When the target does not require scholarly citations, do not demand references",
            rendered,
        )
        self.assertNotIn("You are an academic journal peer reviewer", rendered)
        self.assertNotIn(
            "Identify missing references that could reasonably be expected", rendered
        )

    def test_final_stage_has_no_hard_coded_academic_identity(self):
        final = text("prompts/50_final.md").lower()
        self.assertNotIn("academic journal", final)
        self.assertNotIn("academic rigor", final)
        self.assertIn("selected target", final)
        self.assertIn("do not introduce new concepts", final)

    def test_generic_stages_do_not_encode_any_existing_target_identity(self):
        paths = (
            "prompts/10_draft.md",
            "prompts/20_smooth.md",
            "prompts/30_revise.md",
            "prompts/40_peer_review.md",
            "prompts/50_final.md",
        )
        banned = (
            "academic journal",
            "graduate level",
            "phd level",
            "general-interest magazine",
            "intelligent non-specialists",
            "everyday language",
            "intelligent child",
            "five-year-old",
            "academic rigor",
        )
        for path in paths:
            stage = text(path).lower()
            with self.subTest(stage=path):
                for phrase in banned:
                    self.assertNotIn(phrase, stage)

    def test_missing_target_required_citations_are_fail_closed_not_invented(self):
        for stage in (
            "prompts/10_draft.md",
            "prompts/20_smooth.md",
            "prompts/30_revise.md",
            "prompts/50_final.md",
        ):
            rendered = self.render(stage, "prompts/targets/journal_academic.md")
            with self.subTest(stage=stage):
                self.assertIn("@@FAIL", rendered)
                self.assertIn("requires citation", rendered.lower())
                self.assertIn("authoritative source", rendered.lower())
                self.assertIn("invent", rendered.lower())

    def test_draft_defers_list_realisation_to_target_without_inventing_structure(self):
        draft = text("prompts/10_draft.md")
        self.assertNotIn("Avoid list formatting by default", draft)
        self.assertNotIn(
            "Only emit LaTeX lists when the authoritative source explicitly specifies list structure.",
            draft,
        )
        self.assertIn("Do not mechanically preserve or suppress list formatting", draft)
        self.assertIn("according to the selected target", draft)
        self.assertIn("do not invent conceptual grouping or distinctions", draft)

    def test_target_requirements_cannot_author_new_conceptual_content(self):
        system = text("prompts/00_system.md")
        self.assertIn(
            "Target requirements must never be treated as permission to invent conceptual content, evidence, citations, attributions, conceptual scope, or content-bearing examples.",
            system,
        )
        self.assertIn(
            "may permit reduced coverage only under the coverage and fidelity rules above",
            system,
        )
        self.assertIn(
            "may permit illustrative scaffolding only under the provenance and fidelity rules above",
            system,
        )
        self.assertIn("must not supply evidence or a missing warrant", system)
        journal = text("prompts/targets/journal_academic.md")
        self.assertNotIn("Treat moral language", journal)

    def test_core_coverage_defaults_exhaustive_but_target_can_reduce_it(self):
        system = text("prompts/00_system.md")
        journal = text("prompts/targets/journal_academic.md")
        eli5 = text("prompts/targets/explain_like_im_5.md")
        self.assertIn(
            "Within the core target-driven publication stages, the default is exhaustive conceptual coverage",
            system,
        )
        self.assertIn(
            "An auxiliary transform may define an intrinsic coverage reduction as part of its stage responsibility",
            system,
        )
        self.assertIn("Coverage is exhaustive for this target.", journal)
        self.assertIn("Realise the complete authored argument", journal)
        self.assertIn(
            "explicitly permits summarisation, compression, selective omission, and reordering",
            eli5,
        )
        self.assertIn("one short sitting", eli5)
        self.assertIn("Prefer a short, coherent explanation over exhaustive coverage", eli5)

    def test_magazine_remains_exhaustive_under_generic_default(self):
        magazine = text("prompts/targets/magazine_general.md")
        self.assertIn("Preserve the argument's structure and order.", magazine)
        self.assertIn("Preserve citations supplied by the authoritative source", magazine)
        self.assertNotIn("selective omission", magazine.lower())

    def test_eli5_target_is_literal_short_selective_comprehension_target(self):
        target = text("prompts/targets/explain_like_im_5.md")
        self.assertIn("a curious five-year-old", target)
        self.assertIn("originally conceived for this child", target)
        self.assertIn("summarisation, compression, selective omission", target)
        self.assertIn("one short sitting", target)
        self.assertIn("Rebuild the explanation from concepts the child can already understand", target)
        self.assertIn("Do not preserve adult conceptual packaging", target)
        self.assertIn("Reduce conceptual load as well as linguistic difficulty", target)
        self.assertIn("traceable by an adult reviewer", target)
        self.assertNotIn("intelligent child or adult with no domain knowledge", target)

    def test_citation_presentation_is_target_owned_not_globally_academic(self):
        system = text("prompts/00_system.md")
        journal = text("prompts/targets/journal_academic.md")
        eli5 = text("prompts/targets/explain_like_im_5.md")
        self.assertIn(
            "Evidence, attribution, and citation presentation are realisation responsibilities",
            system,
        )
        self.assertIn("formal citation syntax is not a global fidelity requirement", system)
        self.assertIn(
            "does **not** impose scholarly citation apparatus, academic prose conventions",
            system,
        )
        self.assertIn("Scholarly citation support is required", journal)
        self.assertIn(
            "Use the supplied verified bibliography metadata through formal BibLaTeX citation commands",
            journal,
        )
        self.assertIn(
            "Do not use formal scholarly citation apparatus in the child-facing realisation.",
            eli5,
        )
        self.assertIn("ordinary narrative language that a child can understand", eli5)
        self.assertIn(
            "Do not turn narrative attribution into an appeal to unexplained authority", eli5
        )

    def test_core_stages_do_not_override_target_permitted_scaffolding(self):
        for stage in (
            "prompts/10_draft.md",
            "prompts/20_smooth.md",
            "prompts/30_revise.md",
            "prompts/50_final.md",
        ):
            prompt = text(stage)
            with self.subTest(stage=stage):
                self.assertIn("selected target explicitly permits illustrative scaffolding", prompt)
                self.assertNotIn("Do not add new concepts or examples", prompt)
        review = text("prompts/40_peer_review.md")
        self.assertIn("may be absent from the source without being source drift", review)
        self.assertIn("conceptual density, explanatory progression, overall length", review)
        self.assertIn("not merely vocabulary or sentence length", review)

    def test_core_stages_do_not_force_literal_formal_citation_retention(self):
        for stage in (
            "prompts/10_draft.md",
            "prompts/20_smooth.md",
            "prompts/30_revise.md",
            "prompts/50_final.md",
        ):
            prompt = text(stage)
            with self.subTest(stage=stage):
                self.assertIn("no formal citation apparatus", prompt)
                self.assertIn("narrative attribution", prompt)
        review = text("prompts/40_peer_review.md")
        self.assertIn(
            "Formal scholarly citation apparatus is not globally required", review
        )
        self.assertIn(
            "formal citation apparatus retained when the target explicitly forbids it",
            review,
        )

    def test_peer_review_distinguishes_coverage_from_source_drift(self):
        review = text("prompts/40_peer_review.md")
        self.assertIn(
            "do not classify target-authorised summarisation, compression, or omission as drift merely because source material is absent",
            review,
        )
        self.assertIn("incorrect target coverage", review)
        self.assertIn("source-authored material accidentally omitted", review)
        self.assertIn("REALISATION defect", review)

    def test_existing_academic_target_rules_and_coverage_are_preserved(self):
        journal = text("prompts/targets/journal_academic.md")
        self.assertIn("Coverage is exhaustive for this target.", journal)
        self.assertIn("Do not omit materially distinct claims", journal)
        self.assertIn("without reducing conceptual coverage", journal)
        self.assertIn("Do not oversimplify for accessibility.", journal)
        self.assertIn(
            "Do not appeal to authority except through explicit argument", journal
        )
        self.assertIn(
            "Preserve source-supplied citations for all represented material", journal
        )
        self.assertIn("include a bibliography/reference list", journal)


if __name__ == "__main__":
    unittest.main()
