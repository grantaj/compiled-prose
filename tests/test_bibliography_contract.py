import unittest
from pathlib import Path

from tools.render_prompt import render_prompt

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class BibliographyContractTests(unittest.TestCase):
    def render_with_bibliography(self, target_path: str) -> str:
        return render_prompt(
            system=text("prompts/00_system.md"),
            target=text(target_path),
            stage=text("prompts/10_draft.md"),
            source_text="# Source\nClaim [Known 2020].",
            input_text="# Source\nClaim [Known 2020].",
            output_type="tex",
            bibliography_text="@article{known2020, title={Known}, year={2020}}",
            bibliography_name="references.bib",
        )

    def test_tex_prompt_uses_supplied_bibliography_as_non_conceptual_metadata(self):
        rendered = self.render_with_bibliography(
            "prompts/targets/journal_academic.md"
        )
        self.assertIn(
            "# Citation Metadata (Bibliographic Only; Non-Conceptual)", rendered
        )
        self.assertIn("BIBLIOGRAPHY_RESOURCE: references.bib", rendered)
        self.assertIn("CITATION_PROTOCOL:", rendered)
        self.assertIn("The selected target owns their visible presentation", rendered)
        self.assertIn(
            "If the selected target requires or preserves formal citation apparatus",
            rendered,
        )
        self.assertIn("use biblatex with `backend=biber`", rendered)
        self.assertIn("\\addbibresource{references.bib}", rendered)
        self.assertIn("\\printbibliography", rendered)
        self.assertIn("do not emit a `thebibliography` environment", rendered)

    def test_citation_protocol_allows_target_to_suppress_formal_apparatus(self):
        rendered = self.render_with_bibliography(
            "prompts/targets/explain_like_im_5.md"
        )
        self.assertIn(
            "If the selected target explicitly requires no formal citation apparatus",
            rendered,
        )
        self.assertIn(
            "do not emit biblatex citation commands", rendered
        )
        self.assertIn(
            "Do not use formal scholarly citation apparatus in the child-facing realisation.",
            rendered,
        )
        self.assertIn(
            "use source-authorised narrative attribution only where the retained meaning requires it",
            rendered,
        )

    def test_citation_protocol_does_not_hard_code_target_presentation(self):
        for target_path in (
            "prompts/targets/journal_academic.md",
            "prompts/targets/magazine_general.md",
            "prompts/targets/explain_like_im_5.md",
        ):
            with self.subTest(target=target_path):
                rendered = self.render_with_bibliography(target_path)
                self.assertNotIn("style=authoryear", rendered)
                self.assertNotIn("\\parencite{key}", rendered)
                self.assertNotIn("\\textcite{key}", rendered)
                self.assertIn(
                    "do not hard-code an author-year, numeric, or other presentation",
                    rendered,
                )

    def test_review_receives_metadata_without_tex_output_directives(self):
        rendered = render_prompt(
            system=text("prompts/00_system.md"),
            target=text("prompts/targets/journal_academic.md"),
            stage=text("prompts/40_peer_review.md"),
            source_text="# Source\nClaim [Known 2020].",
            input_text="\\documentclass{article}\\begin{document}x\\end{document}",
            output_type="md",
            bibliography_text="@article{known2020, title={Known}, year={2020}}",
            bibliography_name="references.bib",
        )
        self.assertIn("BIBLIOGRAPHY_RESOURCE: references.bib", rendered)
        self.assertNotIn("CITATION_PROTOCOL:", rendered)
        self.assertIn("OUTPUT_TYPE: md", rendered)

    def test_bibliography_arguments_must_be_paired(self):
        with self.assertRaisesRegex(ValueError, "must be supplied together"):
            render_prompt(
                system="system",
                target="target",
                stage="stage",
                source_text="source",
                input_text="source",
                output_type="tex",
                bibliography_text="@article{x, title={X}}",
            )

    def test_self_build_copies_and_passes_verified_bibliography(self):
        makefile = text("Makefile")
        self.assertIn("SELF_BIBLIOGRAPHY := self-example/references.bib", makefile)
        self.assertIn('cp "$(SELF_BIBLIOGRAPHY)" "$(BUILD_BIBLIOGRAPHY)"', makefile)
        self.assertIn('BIBLIOGRAPHY="$(BUILD_BIBLIOGRAPHY)" final', makefile)
        self.assertIn("--bibliography $(BIBLIOGRAPHY)", makefile)
        self.assertIn('--bibliography "$(SELF_BIBLIOGRAPHY)"', makefile)
        self.assertIn(
            'python tools/self_example_targets.py --path "$(TARGET_STYLE)" --field citation_audit',
            makefile,
        )
        self.assertIn('--citation-retention "$$citation_audit"', makefile)


if __name__ == "__main__":
    unittest.main()
