import unittest
from pathlib import Path

from tools.render_prompt import render_prompt

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class BibliographyContractTests(unittest.TestCase):
    def test_tex_prompt_uses_supplied_bibliography_as_non_conceptual_metadata(self):
        rendered = render_prompt(
            system=text("prompts/00_system.md"),
            target=text("prompts/targets/journal_academic.md"),
            stage=text("prompts/10_draft.md"),
            source_text="# Source\nClaim [Known 2020].",
            input_text="# Source\nClaim [Known 2020].",
            output_type="tex",
            bibliography_text="@article{known2020, title={Known}, year={2020}}",
            bibliography_name="references.bib",
        )
        self.assertIn(
            "# Citation Metadata (Bibliographic Only; Non-Conceptual)", rendered
        )
        self.assertIn("BIBLIOGRAPHY_RESOURCE: references.bib", rendered)
        self.assertIn("\\parencite{key}", rendered)
        self.assertIn(
            "\\usepackage[backend=biber,style=authoryear]{biblatex}", rendered
        )
        self.assertIn("\\addbibresource{references.bib}", rendered)
        self.assertIn("\\printbibliography", rendered)
        self.assertIn("Do not emit a `thebibliography` environment", rendered)

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
        self.assertNotIn("CITATION_FORMAT:", rendered)
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


if __name__ == "__main__":
    unittest.main()
