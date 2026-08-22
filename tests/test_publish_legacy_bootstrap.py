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

    def test_modern_showcase_remains_preferred_after_bootstrap(self):
        modern = self.content.index('"self-example-showcase-"')
        legacy = self.content.index('/^self-example-candidate-[0-9a-f]{40}$/')
        self.assertLess(modern, legacy)
        self.assertIn('core.setOutput("base-kind", "showcase")', self.content)

    def test_selected_academic_target_does_not_reimport_legacy_academic(self):
        self.assertIn(
            "steps.retained.outputs.base-kind == 'legacy-academic' && inputs.target != 'journal_academic'",
            self.content,
        )
        self.assertIn(
            'elif [ "$BASE_KIND" = "legacy-academic" ] && [ "$TARGET_ID" != "journal_academic" ]; then',
            self.content,
        )


if __name__ == "__main__":
    unittest.main()
