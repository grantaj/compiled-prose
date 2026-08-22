import unittest

from tools.self_example_targets import TARGETS, resolve_target


class SelfExampleTargetTests(unittest.TestCase):
    def test_initial_public_target_allowlist_is_exact(self):
        self.assertEqual(
            list(TARGETS),
            ["journal_academic", "magazine_general", "explain_like_im_5"],
        )

    def test_target_paths_are_repository_target_specs(self):
        for identifier, spec in TARGETS.items():
            with self.subTest(identifier=identifier):
                self.assertEqual(spec.identifier, identifier)
                self.assertEqual(spec.path, f"prompts/targets/{identifier}.md")

    def test_eli5_label_matches_literal_target(self):
        self.assertEqual(
            TARGETS["explain_like_im_5"].label, "Explain for a five-year-old"
        )

    def test_unknown_target_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "unsupported self-example target"):
            resolve_target("critical_essay")


if __name__ == "__main__":
    unittest.main()
