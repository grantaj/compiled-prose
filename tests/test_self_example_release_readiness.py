import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = ROOT / "Makefile"


class SelfExampleReleaseReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.makefile = MAKEFILE.read_text(encoding="utf-8")

    def test_self_target_has_fixed_authoritative_source_and_keyless_preflight(self):
        self.assertIn("SELF_SOURCE := outline.md", self.makefile)
        self.assertIn(
            "SELF_SOURCE_AUDIT := self-example/source-audit.json", self.makefile
        )
        self.assertIn(
            "SELF_BIBLIOGRAPHY := self-example/references.bib", self.makefile
        )
        self.assertRegex(self.makefile, r"(?m)^self: self-preflight$")

    def test_self_target_runs_fresh_compile_then_authority_and_latex_checks(self):
        start = self.makefile.index("self: self-preflight")
        end = self.makefile.index("\n# Validation is intentionally", start)
        block = self.makefile[start:end]
        compile_call = (
            'IN="$(SELF_SOURCE)" BIBLIOGRAPHY="$(BUILD_BIBLIOGRAPHY)" final'
        )
        self.assertLess(block.index("clobber"), block.index("cp \"$(SELF_BIBLIOGRAPHY)\""))
        self.assertLess(block.index("cp \"$(SELF_BIBLIOGRAPHY)\""), block.index(compile_call))
        self.assertLess(block.index(compile_call), block.index("--final"))
        self.assertLess(block.index("--final"), block.index("validate-latex"))

    def test_latex_validation_cannot_implicitly_trigger_model_pipeline(self):
        self.assertRegex(self.makefile, r"(?m)^validate-latex:$")
        start = self.makefile.index("validate-latex:")
        end = self.makefile.index("\n# Fast local preflight", start)
        block = self.makefile[start:end]
        self.assertIn('if [ ! -f "$(FINAL_OUT)" ]', block)
        self.assertNotIn("$(FINAL_OUT):", block)
        self.assertNotIn("RUN_STAGE", block)

    def test_source_audit_is_not_model_prompt_input(self):
        match = re.search(r"define RUN_LLM\n(.*?)\nendef", self.makefile, re.DOTALL)
        self.assertIsNotNone(match)
        runner = match.group(1)
        self.assertNotIn("SELF_SOURCE_AUDIT", runner)
        self.assertNotIn("--audit", runner)

    def test_bibliography_is_explicitly_non_authoritative_prompt_metadata(self):
        runner = re.search(
            r"define RUN_LLM\n(.*?)\nendef", self.makefile, re.DOTALL
        ).group(1)
        self.assertIn("--bibliography $(BIBLIOGRAPHY)", runner)
        renderer = (ROOT / "tools/render_prompt.py").read_text(encoding="utf-8")
        self.assertIn("Bibliographic Only; Non-Conceptual", renderer)


if __name__ == "__main__":
    unittest.main()
