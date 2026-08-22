import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.smoke_latex_bibliography import smoke_bibliography


class LatexBibliographySmokeTests(unittest.TestCase):
    def test_smoke_uses_all_entries_from_supplied_bibliography(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bibliography = root / "source.bib"
            diagnostics = root / "diagnostics"
            bibliography.write_text(
                "@book{known, title={Known}, author={A. Author}, year={2020}}\n",
                encoding="utf-8",
            )
            observed: dict[str, str] = {}

            def fake_compile(source, output, *, diagnostic_dir=None):
                observed["source"] = source.read_text(encoding="utf-8")
                observed["bibliography"] = (
                    source.parent / "references.bib"
                ).read_text(encoding="utf-8")
                observed["diagnostic_dir"] = str(diagnostic_dir)
                output.write_bytes(b"pdf")

            with patch(
                "tools.smoke_latex_bibliography.compile_latex",
                side_effect=fake_compile,
            ):
                smoke_bibliography(bibliography, diagnostics)

            self.assertIn("\\nocite{*}", observed["source"])
            self.assertIn("backend=biber", observed["source"])
            self.assertEqual(
                observed["bibliography"],
                bibliography.read_text(encoding="utf-8"),
            )
            self.assertEqual(observed["diagnostic_dir"], str(diagnostics))


if __name__ == "__main__":
    unittest.main()
