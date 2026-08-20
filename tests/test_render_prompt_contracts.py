import ast
import re
import unittest
from pathlib import Path

from tools.render_prompt import render_prompt

ROOT = Path(__file__).resolve().parents[1]

STAGES = {
    "prompts/05_summarize.md": "tex",
    "prompts/10_draft.md": "tex",
    "prompts/20_smooth.md": "tex",
    "prompts/30_revise.md": "tex",
    "prompts/40_peer_review.md": "md",
    "prompts/50_final.md": "tex",
}

TARGETS = (
    "prompts/targets/journal_academic.md",
    "prompts/targets/magazine_general.md",
    "prompts/targets/explain_like_im_5.md",
)


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class RenderPromptContractTests(unittest.TestCase):
    def render(self, stage_path: str, target_path: str, output_type: str) -> str:
        review = (
            "1. MINOR: Test review.\nREVIEW AGAIN: NO"
            if stage_path.endswith("50_final.md")
            else None
        )
        return render_prompt(
            system=text("prompts/00_system.md"),
            target=text(target_path),
            stage=text(stage_path),
            input_text="# Test input\n- one authored claim",
            output_type=output_type,
            review=review,
        )

    def test_every_stage_target_pair_has_one_explicit_contract(self):
        for stage_path, output_type in STAGES.items():
            for target_path in TARGETS:
                with self.subTest(stage=stage_path, target=target_path):
                    rendered = self.render(stage_path, target_path, output_type)
                    self.assertEqual(rendered.count("OUTPUT_TYPE:"), 1)
                    self.assertIn(f"OUTPUT_TYPE: {output_type}", rendered)

    def test_peer_review_contract_is_markdown_only_without_latex_workaround(self):
        for target_path in TARGETS:
            with self.subTest(target=target_path):
                rendered = self.render("prompts/40_peer_review.md", target_path, "md")
                self.assertIn("OUTPUT_TYPE: md", rendered)
                self.assertIn("Return only Markdown content.", rendered)
                self.assertNotIn("Return only the LaTeX output", rendered)
                self.assertNotIn("Output LaTeX only", rendered)
                self.assertNotIn("LaTeX comment", rendered)
                self.assertNotIn("No Markdown", rendered)
                self.assertNotIn("Ignore any global instruction", rendered)

    def test_prose_stages_declare_tex(self):
        for stage_path, output_type in STAGES.items():
            if output_type != "tex":
                continue
            with self.subTest(stage=stage_path):
                rendered = self.render(stage_path, TARGETS[0], output_type)
                self.assertIn("OUTPUT_TYPE: tex", rendered)
                self.assertIn("Return only raw LaTeX content.", rendered)

    def test_target_selection_does_not_change_stage_type(self):
        for stage_path, output_type in STAGES.items():
            contracts = []
            for target_path in TARGETS:
                rendered = self.render(stage_path, target_path, output_type)
                contract = next(
                    line
                    for line in rendered.splitlines()
                    if line.startswith("OUTPUT_TYPE:")
                )
                contracts.append(contract)
            with self.subTest(stage=stage_path):
                self.assertEqual(len(set(contracts)), 1)

    def test_makefile_wires_production_stage_output_types(self):
        makefile = text("Makefile")
        calls = dict(
            re.findall(
                r"\$\(call RUN_LLM,\$\(P_(DRAFT|SMOOTH|REVISE|REVIEW|FINAL)\),"
                r".*?,(tex|md)(?:,|\))",
                makefile,
            )
        )
        self.assertEqual(
            calls,
            {
                "DRAFT": "tex",
                "SMOOTH": "tex",
                "REVISE": "tex",
                "REVIEW": "md",
                "FINAL": "tex",
            },
        )
        self.assertRegex(
            makefile,
            r"--stage prompts/05_summarize\.md .*?--output-type tex",
        )

    def test_final_prompt_with_review_still_has_one_contract(self):
        rendered = self.render("prompts/50_final.md", TARGETS[0], "tex")
        self.assertIn("# Peer Review (Markdown, Diagnostic Only)", rendered)
        self.assertEqual(rendered.count("OUTPUT_TYPE:"), 1)

    def test_renderer_remains_python_39_compatible(self):
        ast.parse(
            text("tools/render_prompt.py"),
            filename="tools/render_prompt.py",
            feature_version=(3, 9),
        )

    def test_unknown_output_type_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unsupported output type"):
            render_prompt(
                system="system",
                target="target",
                stage="stage",
                input_text="input",
                output_type="html",
            )


if __name__ == "__main__":
    unittest.main()
