import shutil
import tempfile
import unittest
from pathlib import Path

from tools.validate_latex import compile_latex, validate_document_text


class LatexValidationTests(unittest.TestCase):
    def test_rejects_failure_sentinel_and_trailing_content(self):
        errors = validate_document_text(
            "\\documentclass{article}\n\\begin{document}\n@@FAIL\n"
            "\\end{document}\ntrailing\n"
        )
        self.assertTrue(any("@@FAIL" in error for error in errors))
        self.assertTrue(any("follows" in error for error in errors))

    def test_rejects_incomplete_document(self):
        errors = validate_document_text("\\documentclass{article}\nhello\n")
        self.assertIn("missing \\begin{document}", errors)
        self.assertIn("missing \\end{document}", errors)

    @unittest.skipUnless(shutil.which("latexmk"), "latexmk not installed")
    def test_real_latexmk_compile_produces_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "final.tex"
            output = root / "final.pdf"
            source.write_text(
                "\\documentclass{article}\n"
                "\\begin{document}\n"
                "A cited claim~\\cite{known}.\n"
                "\\begin{thebibliography}{1}\n"
                "\\bibitem{known} A. Author. Useful Source. 2020.\n"
                "\\end{thebibliography}\n"
                "\\end{document}\n",
                encoding="utf-8",
            )
            compile_latex(source, output)
            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size, 0)

    @unittest.skipUnless(shutil.which("latexmk"), "latexmk not installed")
    def test_real_latexmk_compile_rejects_undefined_citation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "final.tex"
            output = root / "final.pdf"
            source.write_text(
                "\\documentclass{article}\n"
                "\\begin{document}\n"
                "Unsupported citation~\\cite{missing}.\n"
                "\\end{document}\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                RuntimeError, "unresolved LaTeX references/citations"
            ):
                compile_latex(source, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
