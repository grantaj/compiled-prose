import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
REBUILD_WORKFLOW = WORKFLOWS / "rebuild-self-example-showcase.yml"
PUBLISH_WORKFLOW = WORKFLOWS / "publish-self-example.yml"


class ShowcaseRebuildPolicyTests(unittest.TestCase):
    def test_rebuild_is_automatic_only_for_showcase_renderer_changes_on_main(self):
        content = REBUILD_WORKFLOW.read_text(encoding="utf-8")
        trigger_block = content.split("permissions:", 1)[0]

        self.assertIn("push:", trigger_block)
        self.assertIn("      - main\n", trigger_block)
        self.assertIn(
            '      - ".github/workflows/rebuild-self-example-showcase.yml"\n',
            trigger_block,
        )
        self.assertIn('      - "tools/build_self_example_showcase.py"\n', trigger_block)
        self.assertNotIn("build_self_example_*", trigger_block)
        self.assertNotIn("self_example_targets.py", trigger_block)
        self.assertNotIn("workflow_dispatch:", trigger_block)

    def test_rebuild_is_keyless_and_cannot_select_or_compile_prose(self):
        content = REBUILD_WORKFLOW.read_text(encoding="utf-8")

        for forbidden in (
            "OPENAI",
            "BACKEND",
            "secrets.",
            "secrets[",
            "make self",
            "--candidate ",
            "self-example-candidate-",
        ):
            self.assertNotIn(forbidden, content)
        self.assertNotIn("inputs.target", content)
        self.assertNotIn("target:", content.split("permissions:", 1)[0])

    def test_rebuild_uses_last_successful_manual_publication_as_selection(self):
        content = REBUILD_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("listArtifactsForRepo", content)
        self.assertIn("getWorkflowRun", content)
        self.assertIn('artifact.name.startsWith("self-example-showcase-")', content)
        self.assertIn('run.conclusion !== "success"', content)
        self.assertIn('run.event !== "workflow_dispatch"', content)
        self.assertIn(
            'run.path !== ".github/workflows/publish-self-example.yml"', content
        )
        self.assertIn("name: Download accepted showcase", content)
        self.assertIn("--base-showcase base-showcase", content)
        self.assertIn("--expected-outline outline.md", content)
        self.assertIn("cmp -s base-showcase/artifacts/outline.md outline.md", content)

    def test_rebuild_serializes_with_manual_publish(self):
        rebuild = REBUILD_WORKFLOW.read_text(encoding="utf-8")
        publish = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
        group = "group: compiled-prose-self-example-publish"

        self.assertIn(group, rebuild)
        self.assertIn(group, publish)
        self.assertIn("cancel-in-progress: false", rebuild)

    def test_pages_write_authority_is_confined_to_deploy_job(self):
        content = REBUILD_WORKFLOW.read_text(encoding="utf-8")
        rebuild = content.split("  rebuild:", 1)[1].split("  deploy:", 1)[0]
        deploy = content.split("  deploy:", 1)[1]

        self.assertIn("pages: read", rebuild)
        self.assertNotIn("pages: write", rebuild)
        self.assertNotIn("id-token: write", rebuild)
        self.assertIn("pages: write", deploy)
        self.assertIn("id-token: write", deploy)
        self.assertIn("name: github-pages", deploy)
        self.assertIn("actions/deploy-pages@v5", deploy)


if __name__ == "__main__":
    unittest.main()
