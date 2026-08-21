import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.build_self_example_showcase import build_showcase, locate_candidate


class SelfExampleShowcaseTests(unittest.TestCase):
    def make_candidate(
        self,
        root: Path,
        name: str,
        *,
        target: str,
        model: str = "gpt-test",
        source_sha: str = "commit-a",
        outline: str = "# Shared outline\n\n- claim\n",
    ) -> Path:
        candidate = root / name
        artifacts = candidate / "artifacts"
        artifacts.mkdir(parents=True)
        (artifacts / "outline.md").write_text(outline, encoding="utf-8")
        (artifacts / "source-audit.json").write_text("{}\n", encoding="utf-8")
        (artifacts / "references.bib").write_text(
            "@article{x, title={X}}\n", encoding="utf-8"
        )
        (artifacts / "peer_review.md").write_text("STATUS: PASS\n", encoding="utf-8")
        (artifacts / "final.tex").write_text("\\section{Essay}\n", encoding="utf-8")
        (artifacts / "final.pdf").write_bytes(b"%PDF-test")
        (candidate / "build.json").write_text(
            json.dumps(
                {
                    "target": f"prompts/targets/{target}.md",
                    "model": model,
                    "source_sha": source_sha,
                    "workflow_run": f"https://example.invalid/{name}",
                }
            ),
            encoding="utf-8",
        )
        return candidate

    def fake_pandoc(self, command, check):
        self.assertTrue(check)
        output = Path(command[command.index("-o") + 1])
        output.write_text("<html><body>rendered</body></html>\n", encoding="utf-8")

    def test_builds_multi_target_site_from_same_outline_across_different_commits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            academic = self.make_candidate(
                root,
                "academic",
                target="journal_academic",
                source_sha="old-compiler-commit",
                model="gpt-5.6-sol",
            )
            magazine = self.make_candidate(
                root,
                "magazine",
                target="magazine_general",
                source_sha="new-compiler-commit",
            )
            output = root / "site"
            with patch(
                "tools.build_self_example_showcase.subprocess.run",
                side_effect=self.fake_pandoc,
            ) as pandoc:
                build_showcase(
                    candidate_roots={
                        "journal_academic": academic,
                        "magazine_general": magazine,
                    },
                    output_dir=output,
                )

            self.assertEqual(pandoc.call_count, 8)
            self.assertTrue((output / "index.html").is_file())
            self.assertTrue((output / "outline.html").is_file())
            self.assertTrue((output / "artifacts" / "outline.md").is_file())
            for target in ("journal_academic", "magazine_general"):
                target_dir = output / "targets" / target
                self.assertTrue((target_dir / "index.html").is_file())
                self.assertTrue((target_dir / "peer-review.html").is_file())
                self.assertTrue((target_dir / "acceptance.html").is_file())
                self.assertTrue((target_dir / "artifacts" / "final.pdf").is_file())
                self.assertTrue((target_dir / "build.json").is_file())

            manifest = json.loads((output / "showcase.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema"], "compiled-prose-self-example-showcase/1")
            self.assertEqual(
                list(manifest["targets"]), ["journal_academic", "magazine_general"]
            )
            self.assertEqual(
                manifest["targets"]["journal_academic"]["compilation_commit"],
                "old-compiler-commit",
            )
            self.assertEqual(
                manifest["targets"]["magazine_general"]["compilation_commit"],
                "new-compiler-commit",
            )

    def test_different_authoritative_outline_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            academic = self.make_candidate(root, "academic", target="journal_academic")
            magazine = self.make_candidate(
                root,
                "magazine",
                target="magazine_general",
                outline="# Different outline\n",
            )
            with patch("tools.build_self_example_showcase.subprocess.run") as pandoc:
                with self.assertRaisesRegex(ValueError, "authoritative outlines differ"):
                    build_showcase(
                        candidate_roots={
                            "journal_academic": academic,
                            "magazine_general": magazine,
                        },
                        output_dir=root / "site",
                    )
            pandoc.assert_not_called()

    def test_target_metadata_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = self.make_candidate(root, "candidate", target="magazine_general")
            with self.assertRaisesRegex(ValueError, "reports target"):
                build_showcase(
                    candidate_roots={"journal_academic": candidate},
                    output_dir=root / "site",
                )

    def test_download_root_must_contain_exactly_one_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_candidate(root, "one", target="journal_academic")
            self.make_candidate(root, "two", target="journal_academic")
            with self.assertRaisesRegex(ValueError, "exactly one retained candidate"):
                locate_candidate(root)

    def test_empty_candidate_set_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "at least one"):
                build_showcase(candidate_roots={}, output_dir=Path(tmp) / "site")


if __name__ == "__main__":
    unittest.main()
