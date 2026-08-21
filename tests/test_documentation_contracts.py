import re
import shlex
import unittest
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
PIPELINE = ROOT / "pipeline.md"
MAKEFILE = ROOT / "Makefile"

MODEL_TARGETS = {"draft", "smooth", "revise", "review", "final", "summarize"}
STALE_REFERENCES = {
    "PIPELINE_SPEC.md",
    "ERROR_HANDLING.md",
    "context.md",
    "error_handling.md",
    "error_handling_implementation_strategies.md",
    "revised.tex",
}
PROMPT_ASSIGNMENTS = {
    "SYSTEM",
    "TARGET_STYLE",
    "P_DRAFT",
    "P_SMOOTH",
    "P_REVISE",
    "P_REVIEW",
    "P_FINAL",
}


def _phony_targets(makefile: str) -> set[str]:
    targets = set()
    for line in makefile.splitlines():
        if line.startswith(".PHONY:"):
            targets.update(line.partition(":")[2].split())
    return targets


def _documented_make_commands(readme: str):
    for line in readme.splitlines():
        stripped = line.strip()
        if not stripped.startswith("make "):
            continue
        yield stripped, shlex.split(stripped)


def _command_target(tokens: list[str]) -> Optional[str]:
    for token in tokens[1:]:
        if "=" in token and not token.startswith("-"):
            continue
        return token
    return None


def _make_assignment(makefile: str, name: str) -> str:
    match = re.search(rf"^{re.escape(name)}\s*[:?]?=\s*(\S+)\s*$", makefile, re.MULTILINE)
    if match is None:
        raise AssertionError(f"Makefile assignment {name} not found")
    return match.group(1)


class DocumentationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = README.read_text(encoding="utf-8")
        cls.pipeline = PIPELINE.read_text(encoding="utf-8")
        cls.makefile = MAKEFILE.read_text(encoding="utf-8")
        cls.phony_targets = _phony_targets(cls.makefile)

    def test_readme_make_commands_reference_real_targets(self):
        for command, tokens in _documented_make_commands(self.readme):
            target = _command_target(tokens)
            with self.subTest(command=command):
                self.assertIsNotNone(target)
                self.assertIn(target, self.phony_targets)

    def test_model_backed_readme_commands_supply_authoritative_source(self):
        for command, tokens in _documented_make_commands(self.readme):
            target = _command_target(tokens)
            if target not in MODEL_TARGETS:
                continue
            with self.subTest(command=command):
                self.assertTrue(
                    any(token.startswith("IN=") and token != "IN=" for token in tokens[1:]),
                    f"model-backed example must name IN explicitly: {command}",
                )

    def test_makefile_prompt_and_target_paths_exist(self):
        for name in sorted(PROMPT_ASSIGNMENTS):
            relative = _make_assignment(self.makefile, name)
            with self.subTest(assignment=name, path=relative):
                self.assertTrue((ROOT / relative).is_file())

    def test_canonical_pipeline_stage_names_are_make_targets(self):
        for target in ("draft", "smooth", "revise", "review", "final"):
            with self.subTest(target=target):
                self.assertIn(target, self.phony_targets)
                self.assertRegex(
                    self.pipeline,
                    rf"\*\*Make target:\*\* .*`{re.escape(target)}`",
                )

    def test_canonical_docs_do_not_reference_stale_authorities(self):
        canonical_text = self.readme + "\n" + self.pipeline
        for reference in sorted(STALE_REFERENCES):
            with self.subTest(reference=reference):
                self.assertNotIn(reference, canonical_text)


if __name__ == "__main__":
    unittest.main()
