import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLISH_WORKFLOW = ROOT / ".github" / "workflows" / "publish-self-example.yml"


class PublishOutlineCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = PUBLISH_WORKFLOW.read_text(encoding="utf-8")

    def test_legacy_bootstrap_is_removed(self):
        self.assertNotIn("legacyAcademic", self.content)
        self.assertNotIn("legacy-academic", self.content)
        self.assertNotIn("self-example-candidate-[0-9a-f]{40}", self.content)
        self.assertNotIn("Download legacy published academic candidate", self.content)

    def test_selected_candidate_must_match_current_outline(self):
        self.assertIn(
            "if ! cmp -s candidate/artifacts/outline.md outline.md; then",
            self.content,
        )
        self.assertIn(
            "does not use the current authoritative outline",
            self.content,
        )

    def test_compatible_prior_showcase_is_preserved(self):
        self.assertIn(
            "if cmp -s base-showcase/artifacts/outline.md outline.md; then",
            self.content,
        )
        self.assertIn('args+=(--base-showcase base-showcase)', self.content)
        self.assertIn(
            "Preserving compatible unselected targets from publish run",
            self.content,
        )

    def test_stale_showcase_can_be_replaced_by_academic_publication(self):
        self.assertIn(
            'elif [ "$TARGET_ID" = "journal_academic" ]; then',
            self.content,
        )
        self.assertIn(
            "Prior showcase uses an older authoritative outline; starting a new coherent showcase.",
            self.content,
        )

    def test_stale_showcase_requires_academic_first_for_other_targets(self):
        self.assertIn(
            "cannot be mixed with $TARGET_ID",
            self.content,
        )
        self.assertIn(
            "Publish journal_academic first to start a showcase for the current outline",
            self.content,
        )

    def test_latest_means_latest_successful_workflow_run_not_artifact_upload(self):
        self.assertIn("Date.parse(left.run.created_at)", self.content)
        self.assertIn("Date.parse(right.run.created_at)", self.content)
        self.assertNotIn("Date.parse(right.created_at)", self.content)
        self.assertNotIn("Date.parse(left.created_at)", self.content)

    def test_only_selected_target_candidate_is_promoted(self):
        self.assertIn(
            "`self-example-candidate-${target}-`",
            self.content,
        )
        self.assertNotIn("for (const target of", self.content)
        self.assertNotIn("for (const targetId of", self.content)


if __name__ == "__main__":
    unittest.main()
