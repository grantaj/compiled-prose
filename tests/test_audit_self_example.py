import json
import tempfile
import unittest
from pathlib import Path

from tools.audit_self_example import audit


class SelfExampleAuditTests(unittest.TestCase):
    def write_fixture(self, root: Path, *, body_citation="Known 2020", final=None):
        outline = root / "outline.md"
        outline.write_text(
            "# Essay\n\n"
            f"External claim. [{body_citation}]\n\n"
            "## Sources identified for the essay\n\n"
            "**Known 2020**  \nA. Author, Useful Source, 2020.\n\n"
            "Supports the external claim.\n",
            encoding="utf-8",
        )
        audit_file = root / "source-audit.json"
        audit_file.write_text(
            json.dumps(
                {
                    "schema": "compiled-prose-source-audit/1",
                    "authoritative_source": "outline.md",
                    "verified_on": "2026-08-21",
                    "sources": [
                        {
                            "citation": "Known 2020",
                            "bib_key": "known2020",
                            "metadata_status": "verified",
                            "claim_support_status": "verified",
                            "checked_against": ["https://example.invalid/source"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        bibliography = root / "references.bib"
        bibliography.write_text(
            "@article{known2020,\n"
            "  author = {Author, A.},\n"
            "  title = {Useful Source},\n"
            "  year = {2020},\n"
            "}\n",
            encoding="utf-8",
        )
        final_path = None
        if final is not None:
            final_path = root / "final.tex"
            final_path.write_text(final, encoding="utf-8")
        return outline, audit_file, bibliography, final_path

    def test_verified_catalog_and_bibliography_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outline, audit_file, bibliography, _ = self.write_fixture(root)
            result = audit(outline, audit_file, bibliography=bibliography)
            self.assertTrue(result.ok, result.errors)

    def test_unknown_outline_citation_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outline, audit_file, bibliography, _ = self.write_fixture(
                root, body_citation="Invented 2024"
            )
            result = audit(outline, audit_file, bibliography=bibliography)
            self.assertFalse(result.ok)
            self.assertTrue(any("without catalog entries" in error for error in result.errors))

    def test_unverified_source_record_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outline, audit_file, bibliography, _ = self.write_fixture(root)
            data = json.loads(audit_file.read_text(encoding="utf-8"))
            data["sources"][0]["claim_support_status"] = "unchecked"
            audit_file.write_text(json.dumps(data), encoding="utf-8")
            result = audit(outline, audit_file, bibliography=bibliography)
            self.assertFalse(result.ok)
            self.assertIn("Known 2020: claim_support_status is not verified", result.errors)

    def test_bibliography_must_match_audited_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outline, audit_file, bibliography, _ = self.write_fixture(root)
            bibliography.write_text(
                "@article{different2020, title={Different}, year={2020}}\n",
                encoding="utf-8",
            )
            result = audit(outline, audit_file, bibliography=bibliography)
            self.assertFalse(result.ok)
            self.assertTrue(any("missing from .bib" in error for error in result.errors))
            self.assertTrue(any("absent from source audit" in error for error in result.errors))

    def test_final_unknown_explicit_citation_label_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outline, audit_file, bibliography, final = self.write_fixture(
                root,
                final=(
                    "\\documentclass{article}\n\\begin{document}\n"
                    "Known claim [Known 2020]. Invented support [Invented 2024].\n"
                    "\\end{document}\n"
                ),
            )
            result = audit(
                outline, audit_file, bibliography=bibliography, final=final
            )
            self.assertFalse(result.ok)
            self.assertTrue(
                any(
                    "non-authoritative explicit citation labels" in error
                    for error in result.errors
                )
            )

    def test_final_unknown_bibtex_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outline, audit_file, bibliography, final = self.write_fixture(
                root,
                final=(
                    "\\documentclass{article}\n"
                    "\\usepackage[backend=biber,style=authoryear]{biblatex}\n"
                    "\\addbibresource{references.bib}\n"
                    "\\begin{document}\n"
                    "Claim \\footcite{invented2024}.\n"
                    "\\end{document}\n"
                ),
            )
            result = audit(
                outline, audit_file, bibliography=bibliography, final=final
            )
            self.assertFalse(result.ok)
            self.assertTrue(any("unknown bibliography citation keys" in error for error in result.errors))

    def test_final_may_omit_source_citations_without_mechanical_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outline, audit_file, bibliography, final = self.write_fixture(
                root,
                final=(
                    "\\documentclass{article}\n"
                    "\\begin{document}\nTarget-selected explanation without formal citation syntax.\n"
                    "\\end{document}\n"
                ),
            )
            result = audit(
                outline, audit_file, bibliography=bibliography, final=final
            )
            self.assertTrue(result.ok, result.errors)

    def test_formal_citation_may_omit_reference_list_when_target_does_not_require_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outline, audit_file, bibliography, final = self.write_fixture(
                root,
                final=(
                    "\\documentclass{article}\n"
                    "\\usepackage[backend=biber]{biblatex}\n"
                    "\\addbibresource{references.bib}\n"
                    "\\begin{document}\n"
                    "A claim \\fullcite{known2020}.\n"
                    "\\end{document}\n"
                ),
            )
            result = audit(
                outline, audit_file, bibliography=bibliography, final=final
            )
            self.assertTrue(result.ok, result.errors)

    def test_formal_citation_commands_must_bind_to_supplied_bibliography(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outline, audit_file, bibliography, final = self.write_fixture(
                root,
                final=(
                    "\\documentclass{article}\n"
                    "\\begin{document}\n"
                    "A claim \\cite{known2020}.\n"
                    "\\end{document}\n"
                ),
            )
            result = audit(
                outline, audit_file, bibliography=bibliography, final=final
            )
            self.assertFalse(result.ok)
            self.assertTrue(any("must bind formal citation commands" in error for error in result.errors))

    def test_final_with_supplied_bibliography_contract_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outline, audit_file, bibliography, final = self.write_fixture(
                root,
                final=(
                    "\\documentclass{article}\n"
                    "\\usepackage[backend=biber,style=authoryear]{biblatex}\n"
                    "\\addbibresource{references.bib}\n"
                    "\\begin{document}\n"
                    "A claim \\parencite{known2020}.\n"
                    "\\printbibliography\n\\end{document}\n"
                ),
            )
            result = audit(
                outline, audit_file, bibliography=bibliography, final=final
            )
            self.assertTrue(result.ok, result.errors)

    def test_manual_thebibliography_is_rejected_when_metadata_is_supplied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outline, audit_file, bibliography, final = self.write_fixture(
                root,
                final=(
                    "\\documentclass{article}\n"
                    "\\addbibresource{references.bib}\n"
                    "\\begin{document}\n"
                    "A claim \\cite{known2020}.\n"
                    "\\begin{thebibliography}{1}\n"
                    "\\bibitem{known2020} A. Author. Useful Source. 2020.\n"
                    "\\end{thebibliography}\n\\end{document}\n"
                ),
            )
            result = audit(
                outline, audit_file, bibliography=bibliography, final=final
            )
            self.assertFalse(result.ok)
            self.assertTrue(any("must not hand-render" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
