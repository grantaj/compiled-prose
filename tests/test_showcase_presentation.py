import unittest

from tools.build_self_example_showcase import (
    REPOSITORY_URL,
    SHOWCASE_TITLE,
    _landing_markdown,
    _nav_html,
)


class ShowcasePresentationTests(unittest.TestCase):
    def test_navigation_exposes_source_repository(self):
        nav = _nav_html([], prefix="")

        self.assertIn(f'href="{REPOSITORY_URL}"', nav)
        self.assertIn("GitHub repository", nav)
        self.assertIn('class="repo-link"', nav)

    def test_landing_uses_pandoc_title_only_once(self):
        landing = _landing_markdown([])

        self.assertFalse(
            any(line == f"# {SHOWCASE_TITLE}" for line in landing.splitlines())
        )

    def test_landing_also_links_repository_in_body_copy(self):
        landing = _landing_markdown([])

        self.assertIn(f"[GitHub repository]({REPOSITORY_URL})", landing)


if __name__ == "__main__":
    unittest.main()
