import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.build_self_example_site import (
    REQUIRED_ARTIFACTS,
    _prepare_final_tex_for_html,
    build_site,
)


class SelfExampleHtmlRenderingTests(unittest.TestCase):
    def test_html_copy_materializes_embedded_bibliography_citations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "final.tex"
            output = root / "html.tex"
            source.write_text(
                r"""\documentclass{article}
\title{One Canonical Paper Title}
\begin{document}
\maketitle
A claim \cite{lewitt1967,hyland2008}. Another \cite{hyland2008}.
\begin{thebibliography}{9}
\bibitem[LeWitt 1967]{lewitt1967} Sol LeWitt. Sentences on Conceptual Art.
\bibitem{hyland2008} Ken Hyland. Genre and academic writing in the disciplines.
\end{thebibliography}
\end{document}
""",
                encoding="utf-8",
            )

            _prepare_final_tex_for_html(source, output)
            rendered = output.read_text(encoding="utf-8")

            self.assertIn(r"\title{One Canonical Paper Title}", rendered)
            self.assertNotIn(r"\cite{", rendered)
            self.assertNotIn(r"\bibitem", rendered)
            self.assertIn(r"\href{#ref-1}{[LeWitt 1967]}", rendered)
            self.assertIn(r"\href{#ref-2}{[2]}", rendered)
            self.assertIn(r"\section*{References}", rendered)
            self.assertIn(r"\hypertarget{ref-1}{} Sol LeWitt", rendered)
            self.assertIn(r"\hypertarget{ref-2}{} Ken Hyland", rendered)

    def test_html_copy_fails_closed_on_unknown_citation_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "final.tex"
            source.write_text(
                r"""\documentclass{article}
\begin{document}
Claim \cite{missing}.
\begin{thebibliography}{9}
\bibitem{known} Known reference.
\end{thebibliography}
\end{document}
""",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "citation key has no bibitem: missing"):
                _prepare_final_tex_for_html(source, root / "html.tex")

    def test_html_copy_fails_closed_if_citations_have_no_embedded_bibliography(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "final.tex"
            source.write_text(
                r"""\documentclass{article}
\begin{document}
Claim \cite{missing}.
\end{document}
""",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "without an embedded thebibliography"):
                _prepare_final_tex_for_html(source, root / "html.tex")

    def test_final_html_keeps_latex_document_title_instead_of_site_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build = root / "build"
            build.mkdir()
            for name in REQUIRED_ARTIFACTS:
                (build / name).write_text(f"contents of {name}\n", encoding="utf-8")
            (build / "final.tex").write_text(
                r"""\documentclass{article}
\title{Canonical Paper Title}
\begin{document}
\maketitle
Body.
\end{document}
""",
                encoding="utf-8",
            )
            outline = root / "outline.md"
            outline.write_text("# Outline\n", encoding="utf-8")
            source_audit = root / "source-audit.json"
            source_audit.write_text(
                '{"schema":"compiled-prose-source-audit/1"}\n', encoding="utf-8"
            )
            output = root / "docs"
            commands = []

            def fake_pandoc(command, check):
                self.assertTrue(check)
                commands.append(command)
                output_path = Path(command[command.index("-o") + 1])
                output_path.write_text("<html></html>\n", encoding="utf-8")

            with patch(
                "tools.build_self_example_site.subprocess.run",
                side_effect=fake_pandoc,
            ):
                build_site(
                    build_dir=build,
                    outline=outline,
                    source_audit=source_audit,
                    output_dir=output,
                    source_sha="abc123",
                    model="gpt-test",
                    target="prompts/targets/journal_academic.md",
                    run_url="https://example.invalid/run/1",
                )

            index_command = next(
                command
                for command in commands
                if command[command.index("-o") + 1] == str(output / "index.html")
            )
            self.assertNotIn("--metadata", index_command)
            self.assertNotIn("title=Compiled Prose — self-example", index_command)


if __name__ == "__main__":
    unittest.main()
