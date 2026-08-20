import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.build_self_example_site import REQUIRED_ARTIFACTS, build_site


class BuildSelfExampleSiteTests(unittest.TestCase):
    def make_inputs(self, root: Path):
        build = root / "build"
        build.mkdir()
        for name in REQUIRED_ARTIFACTS:
            (build / name).write_text(f"contents of {name}\n", encoding="utf-8")
        outline = root / "outline.md"
        outline.write_text("# Outline\n", encoding="utf-8")
        return build, outline

    def fake_pandoc(self, command, check):
        self.assertTrue(check)
        output = Path(command[command.index("-o") + 1])
        output.write_text(
            "<html><body>rendered</body></html>\n", encoding="utf-8"
        )

    def test_site_contains_rendered_views_raw_artifacts_and_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build, outline = self.make_inputs(root)
            output = root / "docs"
            with patch(
                "tools.build_self_example_site.subprocess.run",
                side_effect=self.fake_pandoc,
            ) as pandoc:
                build_site(
                    build_dir=build,
                    outline=outline,
                    output_dir=output,
                    source_sha="abc123",
                    model="gpt-test",
                    target="prompts/targets/journal_academic.md",
                    run_url="https://example.invalid/run/1",
                )

            self.assertEqual(pandoc.call_count, 3)
            for page in ("index.html", "outline.html", "peer-review.html"):
                self.assertTrue((output / page).is_file())
            for name in REQUIRED_ARTIFACTS:
                self.assertEqual(
                    (output / "artifacts" / name).read_text(encoding="utf-8"),
                    f"contents of {name}\n",
                )
            self.assertEqual(
                (output / "artifacts" / "outline.md").read_text(encoding="utf-8"),
                "# Outline\n",
            )
            metadata = json.loads(
                (output / "build.json").read_text(encoding="utf-8")
            )
            self.assertEqual(metadata["source_sha"], "abc123")
            self.assertEqual(metadata["model"], "gpt-test")
            self.assertTrue((output / ".nojekyll").is_file())

    def test_missing_compilation_artifact_fails_before_pandoc(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build, outline = self.make_inputs(root)
            (build / "final.tex").unlink()
            with patch("tools.build_self_example_site.subprocess.run") as pandoc:
                with self.assertRaisesRegex(FileNotFoundError, "final.tex"):
                    build_site(
                        build_dir=build,
                        outline=outline,
                        output_dir=root / "docs",
                        source_sha="abc",
                        model="model",
                        target="target",
                        run_url="run",
                    )
            pandoc.assert_not_called()


if __name__ == "__main__":
    unittest.main()
