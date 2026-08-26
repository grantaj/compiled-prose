import ast
import unittest
from pathlib import Path

from tools.render_prompt import render_prompt

ROOT = Path(__file__).resolve().parents[1]

STAGES = {
    "prompts/05_summarize.md": "tex",
    "prompts/10_realise.md": "tex",
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
            "STATUS: REVISE_REALISATION\n"
            "- [MINOR][REALISATION] Test paragraph :: Test review."
            if stage_path.endswith("50_final.md")
            else None
        )
        return render_prompt(
            system=text("prompts/00_system.md"),
            target=text(target_path),
            stage=text(stage_path),
            source_text="# Test input\n- one authored claim",
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
                    self.assertEqual(rendered.count("@@FAIL"), 2)

    def test_peer_review_contract_is_markdown_success_without_latex_workaround(self):
        for target_path in TARGETS:
            with self.subTest(target=target_path):
                rendered = self.render("prompts/40_peer_review.md", target_path, "md")
                self.assertIn("OUTPUT_TYPE: md", rendered)
                self.assertIn("SUCCESS: Return only Markdown content.", rendered)
                self.assertNotIn("Return only the LaTeX output", rendered)
                self.assertNotIn("Output LaTeX only", rendered)
                self.assertNotIn("LaTeX comment", rendered)
                self.assertNotIn("Ignore any global instruction", rendered)

    def test_prose_stages_declare_tex_success(self):
        for stage_path, output_type in STAGES.items():
            if output_type != "tex":
                continue
            with self.subTest(stage=stage_path):
                rendered = self.render(stage_path, TARGETS[0], output_type)
                self.assertIn("OUTPUT_TYPE: tex", rendered)
                self.assertIn("SUCCESS: Return exactly one complete raw LaTeX document", rendered)

    def test_failure_contract_is_external_and_authorial(self):
        rendered = self.render("prompts/10_realise.md", TARGETS[0], "tex")
        self.assertIn("Put @@FAIL on the first line", rendered)
        self.assertIn("do not invent or apply a conceptual fix", rendered)
        self.assertIn("rather than embedding diagnostics in LaTeX", rendered)
        self.assertNotIn("% GAP:", rendered)
        self.assertNotIn("% ISSUE:", rendered)

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

    def test_makefile_wires_all_model_stages_through_protocol_enforcement(self):
        makefile = text("Makefile")
        expected_calls = (
            "$(call RUN_STAGE,realise,$(P_REALISE),$(IN),tex,$@)",
            "$(call RUN_STAGE,review,$(P_REVIEW),$(REALISE_OUT),md,$@)",
            "$(call RUN_STAGE,final,$(P_FINAL),$(REALISE_OUT),tex,$@,--review $(REVIEW_OUT))",
            "$(call RUN_STAGE,summarize,prompts/05_summarize.md,$(IN),tex,$@)",
        )
        for call in expected_calls:
            with self.subTest(call=call):
                self.assertIn(call, makefile)
        self.assertIn("--source $(IN) --in $(2)", makefile)
        self.assertIn("python tools/enforce_protocol.py", makefile)
        self.assertIn('--output-type "$(4)"', makefile)
        self.assertIn('--diagnostic "$(ERROR_DIR)/$(1).md"', makefile)
        self.assertIn('--backend-exit-status "$$status"', makefile)
        self.assertIn("python tools/review_decision.py", makefile)
        self.assertEqual(makefile.count("$(call RUN_STAGE,final,"), 1)

    def test_final_prompt_with_review_still_has_one_success_type(self):
        rendered = self.render("prompts/50_final.md", TARGETS[0], "tex")
        self.assertIn("# Peer Review (Markdown, Diagnostic Only)", rendered)
        self.assertIn("STATUS: REVISE_REALISATION", rendered)
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
                source_text="source",
                input_text="input",
                output_type="html",
            )


if __name__ == "__main__":
    unittest.main()
