import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLISH_WORKFLOW = ROOT / ".github" / "workflows" / "publish-self-example.yml"


class LegacyPublishBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = PUBLISH_WORKFLOW.read_text(encoding="utf-8")

    def test_legacy_single_target_publication_is_discoverable(self):
        self.assertIn(
            "/^self-example-candidate-[0-9a-f]{40}$/",
            self.content,
        )
        self.assertIn('".github/workflows/publish-self-example.yml"', self.content)
        self.assertIn('core.setOutput("base-kind", "legacy-academic")', self.content)

    def test_legacy_candidate_bootstraps_without_operator_run_id(self):
        self.assertIn("name: Download legacy published academic candidate", self.content)
        self.assertIn("steps.retained.outputs.base-kind == 'legacy-academic'", self.content)
        self.assertIn('path: legacy-academic', self.content)
        self.assertIn('--candidate "journal_academic=legacy-academic"', self.content)
        self.assertIn('--candidate-run-id "journal_academic=$BASE_RUN_ID"', self.content)

    def test_legacy_academic_is_eligible_as_selected_academic_candidate(self):
        self.assertIn(
            'const candidate = target === "journal_academic"',
            self.content,
        )
        self.assertIn(
            "? newerCandidate(modernCandidate, legacyAcademic)",
            self.content,
        )
        self.assertIn(
            'Publishing ${target} from successful retained compilation run ${candidate.run.id}',
            self.content,
        )

    def test_newer_modern_academic_compile_supersedes_legacy_candidate(self):
        self.assertIn("function newerCandidate(left, right)", self.content)
        self.assertIn("Date.parse(left.run.created_at)", self.content)
        self.assertIn("Date.parse(right.run.created_at)", self.content)
        self.assertIn("right.run.id > left.run.id", self.content)

    def test_modern_showcase_remains_preferred_as_preservation_base(self):
        modern = self.content.index('"self-example-showcase-"')
        base_legacy = self.content.index(
            'if (target !== "journal_academic" && legacyAcademic)'
        )
        self.assertLess(modern, base_legacy)
        self.assertIn('core.setOutput("base-kind", "showcase")', self.content)

    def test_selected_academic_target_does_not_import_legacy_as_a_second_candidate(self):
        self.assertIn(
            'if (target !== "journal_academic" && legacyAcademic)',
            self.content,
        )
        self.assertIn(
            'core.info("No separate prior retained publication base is needed.")',
            self.content,
        )

    def test_latest_means_latest_successful_workflow_run_not_artifact_upload(self):
        self.assertIn("Date.parse(left.run.created_at)", self.content)
        self.assertIn("Date.parse(right.run.created_at)", self.content)
        self.assertNotIn("Date.parse(right.created_at)", self.content)
        self.assertNotIn("Date.parse(left.created_at)", self.content)


if __name__ == "__main__":
    unittest.main()
