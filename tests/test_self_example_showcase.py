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
        run_id: str = "1001",
        include_explicit_ids: bool = True,
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
        metadata = {
            "target": f"prompts/targets/{target}.md",
            "model": model,
            "source_sha": source_sha,
            "workflow_run": f"https://github.com/grantaj/compiled-prose/actions/runs/{run_id}",
        }
        if include_explicit_ids:
            metadata.update(
                {
                    "target_id": target,
                    "target_file": f"prompts/targets/{target}.md",
                    "workflow_run_id": run_id,
                }
            )
        (candidate / "build.json").write_text(json.dumps(metadata), encoding="utf-8")
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
                run_id="101",
            )
            magazine = self.make_candidate(
                root,
                "magazine",
                target="magazine_general",
                source_sha="new-compiler-commit",
                run_id="202",
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
                    candidate_run_ids={
                        "journal_academic": "101",
                        "magazine_general": "202",
                    },
                    output_dir=output,
                )

            self.assertEqual(pandoc.call_count, 10)
            self.assertTrue((output / "index.html").is_file())
            self.assertTrue((output / "outline.html").is_file())
            self.assertTrue((output / "artifacts" / "outline.md").is_file())
            self.assertTrue((output / "peer-review.html").is_file())
            self.assertTrue((output / "acceptance.html").is_file())
            self.assertTrue((output / "artifacts" / "final.pdf").is_file())
            self.assertTrue((output / "artifacts" / "final.tex").is_file())
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
            self.assertEqual(
                manifest["targets"]["journal_academic"]["workflow_run_id"], "101"
            )

    def test_base_showcase_preserves_existing_target_when_adding_another(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            academic = self.make_candidate(
                root, "academic", target="journal_academic", model="gpt-5.6-sol", run_id="101"
            )
            base = root / "base"
            with patch(
                "tools.build_self_example_showcase.subprocess.run",
                side_effect=self.fake_pandoc,
            ):
                build_showcase(
                    candidate_roots={"journal_academic": academic},
                    candidate_run_ids={"journal_academic": "101"},
                    output_dir=base,
                )

            magazine = self.make_candidate(
                root, "magazine", target="magazine_general", run_id="202"
            )
            updated = root / "updated"
            with patch(
                "tools.build_self_example_showcase.subprocess.run",
                side_effect=self.fake_pandoc,
            ):
                build_showcase(
                    candidate_roots={"magazine_general": magazine},
                    candidate_run_ids={"magazine_general": "202"},
                    base_showcase=base,
                    output_dir=updated,
                )

            manifest = json.loads((updated / "showcase.json").read_text(encoding="utf-8"))
            self.assertEqual(
                list(manifest["targets"]), ["journal_academic", "magazine_general"]
            )
            self.assertEqual(
                manifest["targets"]["journal_academic"]["model"], "gpt-5.6-sol"
            )

    def test_explicit_candidate_replaces_same_target_from_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = self.make_candidate(
                root, "old", target="journal_academic", model="old-model", run_id="101"
            )
            base = root / "base"
            with patch(
                "tools.build_self_example_showcase.subprocess.run",
                side_effect=self.fake_pandoc,
            ):
                build_showcase(
                    candidate_roots={"journal_academic": old},
                    candidate_run_ids={"journal_academic": "101"},
                    output_dir=base,
                )
            new = self.make_candidate(
                root, "new", target="journal_academic", model="new-model", run_id="303"
            )
            updated = root / "updated"
            with patch(
                "tools.build_self_example_showcase.subprocess.run",
                side_effect=self.fake_pandoc,
            ):
                build_showcase(
                    candidate_roots={"journal_academic": new},
                    candidate_run_ids={"journal_academic": "303"},
                    base_showcase=base,
                    output_dir=updated,
                )
            manifest = json.loads((updated / "showcase.json").read_text(encoding="utf-8"))
            self.assertEqual(
                manifest["targets"]["journal_academic"]["model"], "new-model"
            )

    def test_first_publication_without_academic_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            magazine = self.make_candidate(root, "magazine", target="magazine_general")
            with self.assertRaisesRegex(ValueError, "journal_academic must remain"):
                build_showcase(
                    candidate_roots={"magazine_general": magazine},
                    output_dir=root / "site",
                )

    def test_candidate_must_match_selected_workflow_run_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            academic = self.make_candidate(
                root, "academic", target="journal_academic", run_id="101"
            )
            with self.assertRaisesRegex(ValueError, "run 202 was selected"):
                build_showcase(
                    candidate_roots={"journal_academic": academic},
                    candidate_run_ids={"journal_academic": "202"},
                    output_dir=root / "site",
                )

    def test_candidate_rejects_inconsistent_run_id_and_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            academic = self.make_candidate(
                root, "academic", target="journal_academic", run_id="101"
            )
            metadata_path = academic / "build.json"
            metadata = json.loads(metadata_path.read_text())
            metadata["workflow_run_id"] = "202"
            metadata_path.write_text(json.dumps(metadata))
            with self.assertRaisesRegex(ValueError, "inconsistent workflow run provenance"):
                build_showcase(
                    candidate_roots={"journal_academic": academic},
                    output_dir=root / "site",
                )

    def test_legacy_candidate_recovers_run_id_from_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            academic = self.make_candidate(
                root,
                "academic",
                target="journal_academic",
                run_id="32450729653",
                include_explicit_ids=False,
            )
            with patch(
                "tools.build_self_example_showcase.subprocess.run",
                side_effect=self.fake_pandoc,
            ):
                build_showcase(
                    candidate_roots={"journal_academic": academic},
                    candidate_run_ids={"journal_academic": "32450729653"},
                    output_dir=root / "site",
                )
            manifest = json.loads((root / "site" / "showcase.json").read_text())
            self.assertEqual(
                manifest["targets"]["journal_academic"]["workflow_run_id"],
                "32450729653",
            )

    def test_candidate_must_match_current_authoritative_outline_when_supplied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            academic = self.make_candidate(root, "academic", target="journal_academic")
            current = root / "outline.md"
            current.write_text("# New current outline\n", encoding="utf-8")
            with patch("tools.build_self_example_showcase.subprocess.run") as pandoc:
                with self.assertRaisesRegex(ValueError, "differs from current source"):
                    build_showcase(
                        candidate_roots={"journal_academic": academic},
                        expected_outline=current,
                        output_dir=root / "site",
                    )
            pandoc.assert_not_called()

    def test_different_authoritative_outline_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            academic = self.make_candidate(root, "academic", target="journal_academic")
            magazine = self.make_candidate(
                root,
                "magazine",
                target="magazine_general",
                outline="# Different outline\n",
                run_id="202",
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
            with self.assertRaisesRegex(ValueError, "target ID"):
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
