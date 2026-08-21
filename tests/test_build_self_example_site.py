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
        source_audit = root / "source-audit.json"
        source_audit.write_text(
            '{"schema":"compiled-prose-source-audit/1"}\n', encoding="utf-8"
        )
        bibliography = root / "references.bib"
        bibliography.write_text(
            "@article{known2020, title={Known}, year={2020}}\n", encoding="utf-8"
        )
        return build, outline, source_audit, bibliography

    def fake_pandoc(self, command, check):
        self.assertTrue(check)
        output = Path(command[command.index("-o") + 1])
        output.write_text("<html><body>rendered</body></html>\n", encoding="utf-8")

    def test_site_contains_rendered_views_raw_artifacts_and_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build, outline, source_audit, bibliography = self.make_inputs(root)
            output = root / "docs"
            with patch(
                "tools.build_self_example_site.subprocess.run",
                side_effect=self.fake_pandoc,
            ) as pandoc:
                build_site(
                    build_dir=build,
                    outline=outline,
                    source_audit=source_audit,
                    bibliography=bibliography,
                    output_dir=output,
                    source_sha="abc123",
                    model="gpt-test",
                    target="prompts/targets/journal_academic.md",
                    target_id="journal_academic",
                    run_url="https://github.com/grantaj/compiled-prose/actions/runs/12345",
                    run_id="12345",
                )

            self.assertEqual(pandoc.call_count, 4)
            for page in ("index.html", "outline.html", "peer-review.html", "acceptance.html"):
                self.assertTrue((output / page).is_file())
            for name in REQUIRED_ARTIFACTS:
                self.assertEqual(
                    (output / "artifacts" / name).read_text(encoding="utf-8"),
                    f"contents of {name}\n",
                )
            metadata = json.loads((output / "build.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["source_sha"], "abc123")
            self.assertEqual(metadata["model"], "gpt-test")
            self.assertEqual(metadata["target"], "prompts/targets/journal_academic.md")
            self.assertEqual(metadata["target_file"], "prompts/targets/journal_academic.md")
            self.assertEqual(metadata["target_id"], "journal_academic")
            self.assertEqual(metadata["workflow_run_id"], "12345")
            self.assertIn("built_at_utc", metadata)
            self.assertNotIn("published_at_utc", metadata)
            self.assertEqual(metadata["authoritative_source"], "outline.md")
            self.assertEqual(metadata["source_audit"], "source-audit.json")
            self.assertEqual(metadata["bibliography"], "references.bib")
            self.assertTrue((output / ".nojekyll").is_file())

    def test_legacy_optional_metadata_remains_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build, outline, source_audit, bibliography = self.make_inputs(root)
            with patch(
                "tools.build_self_example_site.subprocess.run",
                side_effect=self.fake_pandoc,
            ):
                build_site(
                    build_dir=build,
                    outline=outline,
                    source_audit=source_audit,
                    bibliography=bibliography,
                    output_dir=root / "docs",
                    source_sha="abc",
                    model="model",
                    target="prompts/targets/journal_academic.md",
                    run_url="https://github.com/grantaj/compiled-prose/actions/runs/9",
                )
            metadata = json.loads((root / "docs" / "build.json").read_text())
            self.assertNotIn("target_id", metadata)
            self.assertNotIn("workflow_run_id", metadata)

    def test_missing_compilation_artifact_fails_before_pandoc(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build, outline, source_audit, bibliography = self.make_inputs(root)
            (build / "final.pdf").unlink()
            with patch("tools.build_self_example_site.subprocess.run") as pandoc:
                with self.assertRaisesRegex(FileNotFoundError, "final.pdf"):
                    build_site(
                        build_dir=build,
                        outline=outline,
                        source_audit=source_audit,
                        bibliography=bibliography,
                        output_dir=root / "docs",
                        source_sha="abc",
                        model="model",
                        target="target",
                        run_url="run",
                    )
            pandoc.assert_not_called()

    def test_missing_source_audit_fails_before_pandoc(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build, outline, source_audit, bibliography = self.make_inputs(root)
            source_audit.unlink()
            with patch("tools.build_self_example_site.subprocess.run") as pandoc:
                with self.assertRaisesRegex(FileNotFoundError, "source-audit.json"):
                    build_site(
                        build_dir=build,
                        outline=outline,
                        source_audit=source_audit,
                        bibliography=bibliography,
                        output_dir=root / "docs",
                        source_sha="abc",
                        model="model",
                        target="target",
                        run_url="run",
                    )
            pandoc.assert_not_called()

    def test_missing_bibliography_fails_before_pandoc(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build, outline, source_audit, bibliography = self.make_inputs(root)
            bibliography.unlink()
            with patch("tools.build_self_example_site.subprocess.run") as pandoc:
                with self.assertRaisesRegex(FileNotFoundError, "references.bib"):
                    build_site(
                        build_dir=build,
                        outline=outline,
                        source_audit=source_audit,
                        bibliography=bibliography,
                        output_dir=root / "docs",
                        source_sha="abc",
                        model="model",
                        target="target",
                        run_url="run",
                    )
            pandoc.assert_not_called()


if __name__ == "__main__":
    unittest.main()
