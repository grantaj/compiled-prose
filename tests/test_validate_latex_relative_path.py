import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.validate_latex import compile_latex


class LatexRelativePathTests(unittest.TestCase):
    def test_relative_input_uses_source_local_absolute_outdir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build = root / "build"
            build.mkdir()
            (build / "final.tex").write_text(
                "\\documentclass{article}\n"
                "\\begin{document}\n"
                "Relative path fixture.\n"
                "\\end{document}\n",
                encoding="utf-8",
            )
            original_cwd = Path.cwd()

            def fake_run(command, **kwargs):
                self.assertEqual(Path(kwargs["cwd"]), build.resolve())
                outdir = Path(
                    next(
                        arg.split("=", 1)[1]
                        for arg in command
                        if arg.startswith("-outdir=")
                    )
                )
                self.assertTrue(outdir.is_absolute())
                self.assertEqual(outdir.parent, build.resolve())
                (outdir / "final.log").write_text("clean log\n", encoding="utf-8")
                (outdir / "final.pdf").write_bytes(b"pdf")
                return subprocess.CompletedProcess(command, 0, stdout="")

            try:
                os.chdir(root)
                with patch(
                    "tools.validate_latex.shutil.which", return_value="/fake/latexmk"
                ):
                    with patch(
                        "tools.validate_latex.subprocess.run", side_effect=fake_run
                    ):
                        compile_latex(Path("build/final.tex"), Path("build/final.pdf"))
                self.assertEqual(Path("build/final.pdf").read_bytes(), b"pdf")
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
