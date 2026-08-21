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
                            "metadata_status": "verified",
                            "claim_support_status": "verified",
                            "checked_against": ["https://example.invalid/source"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        final_path = None
        if final is not None:
            final_path = root / "final.tex"
            final_path.write_text(final, encoding="utf-8")
        return outline, audit_file, final_path

    def test_verified_catalog_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outline, audit_file, _ = self.write_fixture(root)
            result = audit(outline, audit_file)
            self.assertTrue(result.ok, result.errors)

    def test_unknown_outline_citation_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outline, audit_file, _ = self.write_fixture(root, body_citation="Invented 2024")
            result = audit(outline, audit_file)
            self.assertFalse(result.ok)
            self.assertTrue(any("without catalog entries" in error for error in result.errors))

    def test_unverified_source_record_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outline, audit_file, _ = self.write_fixture(root)
            data = json.loads(audit_file.read_text(encoding="utf-8"))
            data["sources"][0]["claim_support_status"] = "unchecked"
            audit_file.write_text(json.dumps(data), encoding="utf-8")
            result = audit(outline, audit_file)
            self.assertFalse(result.ok)
            self.assertIn("Known 2020: claim_support_status is not verified", result.errors)

    def test_final_unknown_explicit_citation_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outline, audit_file, final = self.write_fixture(
                root,
                final=(
                    "\\documentclass{article}\n\\begin{document}\n"
                    "Known claim [Known 2020]. Invented support [Invented 2024].\n"
                    "\\end{document}\n"
                ),
            )
            result = audit(outline, audit_file, final=final)
            self.assertFalse(result.ok)
            self.assertTrue(
                any(
                    "non-authoritative explicit citation labels" in error
                    for error in result.errors
                )
            )

    def test_final_allows_latex_citation_keys_without_guessing_their_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outline, audit_file, final = self.write_fixture(
                root,
                final=(
                    "\\documentclass{article}\n\\begin{document}\n"
                    "A claim~\\cite{source1}.\n"
                    "\\begin{thebibliography}{1}\n"
                    "\\bibitem{source1} A. Author. Useful Source. 2020.\n"
                    "\\end{thebibliography}\n\\end{document}\n"
                ),
            )
            result = audit(outline, audit_file, final=final)
            self.assertTrue(result.ok, result.errors)


if __name__ == "__main__":
    unittest.main()
