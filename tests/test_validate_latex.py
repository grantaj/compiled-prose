import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_failed_compile_surfaces_and_retains_actionable_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "final.tex"
            output = root / "final.pdf"
            diagnostic_dir = root / "errors" / "latex"
            source.write_text(
                "\\documentclass{article}\n"
                "\\begin{document}\n"
                "Failure fixture.\n"
                "\\end{document}\n",
                encoding="utf-8",
            )

            def fake_run(command, **kwargs):
                del kwargs
                outdir = Path(
                    next(
                        arg.split("=", 1)[1]
                        for arg in command
                        if arg.startswith("-outdir=")
                    )
                )
                self.assertEqual(outdir.parent, root)
                (outdir / "final.log").write_text(
                    "before\n"
                    "pdfTeX error (font expansion): auto expansion is only possible "
                    "with scalable fonts.\n"
                    "after\n",
                    encoding="utf-8",
                )
                (outdir / "final.bbl-SAVE-ERROR").write_text(
                    "saved broken bbl\n", encoding="utf-8"
                )
                (outdir / "final.bcf-SAVE-ERROR").write_text(
                    "saved broken bcf\n", encoding="utf-8"
                )
                (outdir / "final.blg").write_text(
                    "biber details\n", encoding="utf-8"
                )
                return subprocess.CompletedProcess(
                    command, 12, stdout="latexmk summary without root cause\n"
                )

            with patch(
                "tools.validate_latex.shutil.which", return_value="/fake/latexmk"
            ):
                with patch(
                    "tools.validate_latex.subprocess.run", side_effect=fake_run
                ):
                    with self.assertRaisesRegex(RuntimeError, "pdfTeX error"):
                        compile_latex(
                            source,
                            output,
                            diagnostic_dir=diagnostic_dir,
                        )

            self.assertEqual(
                (diagnostic_dir / "final.bbl-SAVE-ERROR").read_text(
                    encoding="utf-8"
                ),
                "saved broken bbl\n",
            )
            self.assertEqual(
                (diagnostic_dir / "final.bcf-SAVE-ERROR").read_text(
                    encoding="utf-8"
                ),
                "saved broken bcf\n",
            )
            self.assertEqual(
                (diagnostic_dir / "final.blg").read_text(encoding="utf-8"),
                "biber details\n",
            )
            self.assertIn(
                "latexmk summary",
                (diagnostic_dir / "latexmk.stdout.txt").read_text(encoding="utf-8"),
            )

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
