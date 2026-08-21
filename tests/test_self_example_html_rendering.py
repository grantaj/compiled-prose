import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.build_self_example_site import REQUIRED_ARTIFACTS, build_site

ROOT = Path(__file__).resolve().parents[1]


class SelfExampleHtmlRenderingTests(unittest.TestCase):
    def make_inputs(self, root: Path):
        build = root / "build"
        build.mkdir()
        for name in REQUIRED_ARTIFACTS:
            (build / name).write_text(f"contents of {name}\n", encoding="utf-8")
        (build / "final.tex").write_text(
            r"""\documentclass{article}
\usepackage[backend=biber,style=authoryear]{biblatex}
\addbibresource{references.bib}
\title{Canonical Paper Title}
\begin{document}
\maketitle
A claim \parencite{known2020}.
\printbibliography
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
        bibliography = root / "references.bib"
        bibliography.write_text(
            "@article{known2020, author={Author, A.}, title={Known}, year={2020}}\n",
            encoding="utf-8",
        )
        return build, outline, source_audit, bibliography

    def fake_pandoc(self, commands):
        def run(command, check):
            self.assertTrue(check)
            commands.append(command)
            output_path = Path(command[command.index("-o") + 1])
            output_path.write_text("<html></html>\n", encoding="utf-8")

        return run

    def test_final_html_uses_native_citeproc_and_same_bibliography(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build, outline, source_audit, bibliography = self.make_inputs(root)
            output = root / "docs"
            commands = []

            with patch(
                "tools.build_self_example_site.subprocess.run",
                side_effect=self.fake_pandoc(commands),
            ):
                build_site(
                    build_dir=build,
                    outline=outline,
                    source_audit=source_audit,
                    bibliography=bibliography,
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
            self.assertIn("--citeproc", index_command)
            self.assertIn(f"--bibliography={bibliography}", index_command)
            self.assertNotIn("--metadata", index_command)
            self.assertNotIn("title=Compiled Prose — self-example", index_command)

    def test_non_final_pages_do_not_inherit_paper_bibliography(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build, outline, source_audit, bibliography = self.make_inputs(root)
            output = root / "docs"
            commands = []

            with patch(
                "tools.build_self_example_site.subprocess.run",
                side_effect=self.fake_pandoc(commands),
            ):
                build_site(
                    build_dir=build,
                    outline=outline,
                    source_audit=source_audit,
                    bibliography=bibliography,
                    output_dir=output,
                    source_sha="abc123",
                    model="gpt-test",
                    target="target",
                    run_url="run",
                )

            non_final = [
                command
                for command in commands
                if command[command.index("-o") + 1] != str(output / "index.html")
            ]
            self.assertTrue(non_final)
            for command in non_final:
                self.assertNotIn("--citeproc", command)
                self.assertFalse(any(arg.startswith("--bibliography=") for arg in command))

    def test_candidate_retains_bibliography_as_non_conceptual_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build, outline, source_audit, bibliography = self.make_inputs(root)
            output = root / "docs"

            with patch(
                "tools.build_self_example_site.subprocess.run",
                side_effect=self.fake_pandoc([]),
            ):
                build_site(
                    build_dir=build,
                    outline=outline,
                    source_audit=source_audit,
                    bibliography=bibliography,
                    output_dir=output,
                    source_sha="abc123",
                    model="gpt-test",
                    target="target",
                    run_url="run",
                )

            self.assertEqual(
                (output / "artifacts" / "references.bib").read_text(encoding="utf-8"),
                bibliography.read_text(encoding="utf-8"),
            )
            metadata = json.loads((output / "build.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["bibliography"], "references.bib")

    def test_site_builder_has_no_bespoke_citation_parser_or_rewriter(self):
        builder = (ROOT / "tools/build_self_example_site.py").read_text(encoding="utf-8")
        for forbidden in (
            "_prepare_final_tex_for_html",
            "_BIBITEM_RE",
            "_SIMPLE_CITE_RE",
            "thebibliography environment",
            "replace_cite",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, builder)
        self.assertIn("--citeproc", builder)
        self.assertIn("--bibliography=", builder)


if __name__ == "__main__":
    unittest.main()
