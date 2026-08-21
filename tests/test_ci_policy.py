import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
PAID_WORKFLOW = WORKFLOWS / "publish-self-example.yml"


class CiSpendingPolicyTests(unittest.TestCase):
    def test_only_manual_publication_workflow_can_reference_paid_provider(self):
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

    def test_paid_workflow_has_no_automatic_trigger(self):
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

    def test_paid_workflow_requires_explicit_authorization_and_environment_gate(self):
        content = PAID_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("authorize_paid_api_call:", content)
        self.assertIn("default: false", content)
        self.assertIn("github.actor == github.repository_owner", content)
        self.assertIn("github.ref == 'refs/heads/main'", content)
        self.assertIn("inputs.authorize_paid_api_call == true", content)
        self.assertIn("environment: paid-compilation", content)
        self.assertIn("OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}", content)
        self.assertIn('OPENAI_MAX_OUTPUT_TOKENS: "20000"', content)
        self.assertIn("pages: read", content)
        self.assertLess(
            content.index("Verify GitHub Pages configuration"),
            content.index("Paid compilation"),
        )

    def test_paid_workflow_uses_release_ready_self_command(self):
        content = PAID_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("run: make check", content)
        self.assertIn('TARGET_STYLE="$TARGET_STYLE" self', content)
        self.assertIn("latexmk", content)
        self.assertIn("--source-audit self-example/source-audit.json", content)

    def test_failed_paid_compilation_surfaces_and_retains_diagnostics(self):
        content = PAID_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("id: compile_self_example", content)
        self.assertIn('compgen -G "build/errors/*.md"', content)
        self.assertIn('cat "$diagnostic" || true', content)
        self.assertIn(
            "if: ${{ failure() && steps.compile_self_example.outcome == 'failure' }}",
            content,
        )
        self.assertIn(
            "name: self-example-failure-${{ github.sha }}-${{ github.run_id }}",
            content,
        )
        self.assertIn("            build\n", content)
        self.assertIn("            outline.md\n", content)
        self.assertIn("            self-example/source-audit.json\n", content)
        self.assertIn("if-no-files-found: warn", content)
        self.assertIn("retention-days: 90", content)
        self.assertLess(
            content.index("Upload failed self-example evidence"),
            content.index("Build inspectable acceptance candidate"),
        )

    def test_candidate_is_retained_before_human_gated_deployment(self):
        content = PAID_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("actions/upload-artifact@v4", content)
        self.assertIn("name: self-example-candidate-${{ github.sha }}", content)
        self.assertIn("include-hidden-files: true", content)
        self.assertIn("retention-days: 90", content)
        self.assertIn("name: github-pages", content)
        self.assertLess(
            content.index("Upload self-example acceptance candidate"),
            content.index("deploy:"),
        )

    def test_ordinary_ci_is_keyless_and_read_only(self):
        content = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("contents: read", content)
        self.assertIn('python-version: "3.9"', content)
        self.assertIn("run: make check", content)
        self.assertNotIn("workflow_dispatch", content)
        self.assertNotIn("pages: write", content)


if __name__ == "__main__":
    unittest.main()
