import unittest
from pathlib import Path

from tools.build_self_example_showcase import (
    REPOSITORY_URL,
    SHOWCASE_TITLE,
    _landing_markdown,
    _nav_html,
)

ROOT = Path(__file__).resolve().parents[1]
SHOWCASE_THEME = ROOT / "tools" / "showcase_theme.css"


class ShowcasePresentationTests(unittest.TestCase):
    def test_navigation_exposes_source_repository(self):
        nav = _nav_html([], prefix="")

        self.assertIn(f'href="{REPOSITORY_URL}"', nav)
        self.assertIn("GitHub repository", nav)
        self.assertIn('class="repo-link"', nav)

    def test_navigation_uses_plain_public_labels(self):
        nav = _nav_html([], prefix="")

        self.assertIn(">About</a>", nav)
        self.assertIn(">Outline</a>", nav)
        self.assertNotIn("Showcase", nav)
        self.assertNotIn("Authoritative outline", nav)

    def test_navigation_layout_does_not_use_auto_margin(self):
        theme = SHOWCASE_THEME.read_text(encoding="utf-8")

        self.assertIn("nav .repo-link {\n  margin-left: 0;\n}", theme)
        self.assertNotIn("nav .repo-link {\n  margin-left: auto;", theme)

    def test_narrow_navigation_uses_stable_two_column_grid(self):
        theme = SHOWCASE_THEME.read_text(encoding="utf-8")

        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr));", theme)
        self.assertIn("white-space: normal;", theme)

    def test_landing_uses_pandoc_title_only_once(self):
        landing = _landing_markdown([])

        self.assertEqual("Compiled Prose", SHOWCASE_TITLE)
        self.assertFalse(
            any(line == f"# {SHOWCASE_TITLE}" for line in landing.splitlines())
        )

    def test_landing_orients_without_old_meta_labels(self):
        landing = _landing_markdown([])
        lower = landing.lower()

        self.assertIn("The outline used here is itself about Compiled Prose.", landing)
        self.assertNotIn("showcase", lower)
        self.assertNotIn("self-example", lower)
        self.assertNotIn("authoritative outline", lower)

    def test_landing_also_links_repository_in_body_copy(self):
        landing = _landing_markdown([])

        self.assertIn(f"[GitHub repository]({REPOSITORY_URL})", landing)


if __name__ == "__main__":
    unittest.main()
