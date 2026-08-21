import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
PAID_WORKFLOW = WORKFLOWS / "compile-self-example.yml"
PUBLISH_WORKFLOW = WORKFLOWS / "publish-self-example.yml"


class CiSpendingPolicyTests(unittest.TestCase):
    def test_only_compile_workflow_can_reference_paid_provider(self):
        workflows = sorted(
            list(WORKFLOWS.glob("*.yml")) + list(WORKFLOWS.glob("*.yaml"))
        )
        for workflow in workflows:
            content = workflow.read_text(encoding="utf-8")
            with self.subTest(workflow=workflow.name):
                if workflow == PAID_WORKFLOW:
                    self.assertIn("OPENAI_API_KEY", content)
                    self.assertIn("BACKEND: openai", content)
                else:
                    self.assertNotIn("OPENAI_API_KEY", content)
                    self.assertNotIn("BACKEND: openai", content)
                    self.assertNotIn("secrets.", content)
                    self.assertNotIn("secrets[", content)

    def test_compile_workflow_has_no_automatic_trigger(self):
        content = PAID_WORKFLOW.read_text(encoding="utf-8")
        trigger_block = content.split("permissions:", 1)[0]
        self.assertIn("workflow_dispatch:", trigger_block)
        for forbidden in (
            "push",
            "pull_request",
            "schedule",
            "workflow_run",
            "repository_dispatch",
            "workflow_call",
        ):
            self.assertNotIn(forbidden, trigger_block)

    def test_compile_workflow_requires_explicit_authorization_and_environment_gate(self):
        content = PAID_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("authorize_paid_api_call:", content)
        self.assertIn("default: false", content)
        self.assertIn("github.actor == github.repository_owner", content)
        self.assertIn("github.ref == 'refs/heads/main'", content)
        self.assertIn("inputs.authorize_paid_api_call == true", content)
        self.assertIn("environment: paid-compilation", content)
        self.assertIn("OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}", content)
        self.assertIn('OPENAI_MAX_OUTPUT_TOKENS: "10000"', content)

    def test_compile_workflow_model_selection_is_constrained(self):
        content = PAID_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("openai_model:", content)
        self.assertIn('description: "OpenAI model"', content)
        self.assertIn("type: choice", content)
        self.assertIn("default: gpt-5-mini", content)
        for model in (
            "gpt-5-mini",
            "gpt-5",
            "gpt-5.6-luna",
            "gpt-5.6-terra",
            "gpt-5.6-sol",
        ):
            self.assertIn(f"          - {model}\n", content)
        self.assertIn("OPENAI_MODEL: ${{ inputs.openai_model }}", content)
        self.assertIn("name: Validate selected OpenAI model", content)
        self.assertIn(
            "gpt-5-mini|gpt-5|gpt-5.6-luna|gpt-5.6-terra|gpt-5.6-sol",
            content,
        )
        self.assertLess(
            content.index("Validate selected OpenAI model"),
            content.index("OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}"),
        )

    def test_compile_workflow_target_selection_is_constrained_before_secret(self):
        content = PAID_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("target:", content)
        self.assertIn('description: "Compilation target"', content)
        self.assertIn("default: journal_academic", content)
        for target in (
            "journal_academic",
            "magazine_general",
            "explain_like_im_5",
        ):
            self.assertIn(f"          - {target}\n", content)
        self.assertIn("tools/self_example_targets.py", content)
        self.assertIn("TARGET_STYLE: ${{ needs.preflight.outputs.target_style }}", content)
        self.assertLess(
            content.index("Resolve and validate selected target"),
            content.index("OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}"),
        )

    def test_compile_workflow_builds_candidate_but_never_publishes_pages(self):
        content = PAID_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("run: make check", content)
        self.assertIn('TARGET_STYLE="$TARGET_STYLE" self', content)
        self.assertIn("latexmk", content)
        self.assertIn("texlive-bibtex-extra", content)
        self.assertIn("biber", content)
        self.assertIn("--source-audit self-example/source-audit.json", content)
        self.assertIn("--bibliography self-example/references.bib", content)
        self.assertIn("--output-dir candidate", content)
        self.assertIn("Upload retained self-example candidate", content)
        self.assertIn(
            "self-example-candidate-${{ inputs.target }}-${{ inputs.openai_model }}-${{ github.sha }}-${{ github.run_id }}",
            content,
        )
        self.assertNotIn("upload-pages-artifact", content)
        self.assertNotIn("deploy-pages", content)
        self.assertNotIn("environment:\n      name: github-pages", content)

    def test_compile_workflow_always_summarizes_and_retains_failures(self):
        content = PAID_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("name: Summarize paid API usage", content)
        summary_start = content.index("- name: Summarize paid API usage")
        summary_end = content.index("- name: Upload failed self-example evidence")
        block = content[summary_start:summary_end]
        self.assertIn("if: ${{ always() }}", block)
        self.assertIn("tools/summarize_openai_usage.py", block)
        self.assertIn("$GITHUB_STEP_SUMMARY", block)
        self.assertIn("id: compile_self_example", content)
        self.assertIn('compgen -G "build/errors/*.md"', content)
        self.assertIn("retention-days: 90", content)

    def test_publish_workflow_is_manual_keyless_and_provider_free(self):
        content = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        trigger_block = content.split("permissions:", 1)[0]
        self.assertIn("workflow_dispatch:", trigger_block)
        self.assertNotIn("OPENAI", content)
        self.assertNotIn("BACKEND", content)
        self.assertNotIn("secrets.", content)
        self.assertNotIn("tools/llm_run", content)
        self.assertNotIn("make self", content)
        for forbidden in ("push", "pull_request", "schedule", "workflow_run"):
            self.assertNotIn(forbidden, trigger_block)

    def test_publish_workflow_uses_explicit_compile_run_ids_and_showcase_builder(self):
        content = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("base_publish_run_id:", content)
        self.assertIn("pattern: self-example-showcase-*", content)
        self.assertIn("run-id: ${{ inputs.base_publish_run_id }}", content)
        self.assertIn("--base-showcase base-showcase", content)
        for target in (
            "journal_academic",
            "magazine_general",
            "explain_like_im_5",
        ):
            self.assertIn(f"{target}_run_id:", content)
            self.assertIn(f'--candidate "{target}=candidates/{target}"', content)
        self.assertIn("actions/download-artifact@v4", content)
        self.assertIn("run-id: ${{ inputs.journal_academic_run_id }}", content)
        self.assertIn("run-id: ${{ inputs.magazine_general_run_id }}", content)
        self.assertIn("run-id: ${{ inputs.explain_like_im_5_run_id }}", content)
        self.assertIn("tools/build_self_example_showcase.py", content)
        self.assertNotIn("latest candidate", content.lower())
        self.assertNotIn("/latest", content.lower())

    def test_publish_workflow_deploys_only_assembled_retained_site(self):
        content = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Upload inspectable publication bundle", content)
        self.assertIn("actions/upload-pages-artifact@v5", content)
        self.assertIn("actions/deploy-pages@v5", content)
        self.assertIn("name: github-pages", content)
        self.assertLess(
            content.index("Assemble multi-target Pages site"),
            content.index("Upload Pages artifact"),
        )
        self.assertLess(content.index("Upload Pages artifact"), content.index("deploy:"))

    def test_ordinary_ci_is_keyless_and_read_only(self):
        content = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("contents: read", content)
        self.assertIn('python-version: "3.9"', content)
        self.assertIn("run: make check", content)
        self.assertNotIn("workflow_dispatch", content)
        self.assertNotIn("pages: write", content)


if __name__ == "__main__":
    unittest.main()
