import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAID_WORKFLOW = ROOT / ".github" / "workflows" / "compile-self-example.yml"


class PaidLatexPreflightPolicyTests(unittest.TestCase):
    def test_bibliography_smoke_is_keyless_and_precedes_paid_secret(self):
        content = PAID_WORKFLOW.read_text(encoding="utf-8")
        preflight = content.split("  preflight:", 1)[1].split("  compile:", 1)[0]
        smoke = "- name: Smoke-test LaTeX bibliography toolchain"
        secret = "OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}"

        self.assertIn(smoke, preflight)
        self.assertIn("tools/smoke_latex_bibliography.py", preflight)
        self.assertIn("self-example/references.bib", preflight)
        self.assertIn("build/errors/latex-smoke", preflight)
        self.assertIn("Upload keyless preflight diagnostics", preflight)
        self.assertNotIn("OPENAI_API_KEY", preflight)
        self.assertNotIn("secrets.", preflight)
        self.assertLess(content.index(smoke), content.index(secret))

    def test_release_validation_installs_scalable_t1_fonts_in_both_jobs(self):
        content = PAID_WORKFLOW.read_text(encoding="utf-8")
        preflight = content.split("  preflight:", 1)[1].split("  compile:", 1)[0]
        paid_job = content.split("  compile:", 1)[1]

        self.assertIn("cm-super", preflight)
        self.assertIn("cm-super", paid_job)

    def test_paid_job_still_depends_on_successful_preflight(self):
        content = PAID_WORKFLOW.read_text(encoding="utf-8")
        paid_job = content.split("  compile:", 1)[1]
        self.assertIn("needs: preflight", paid_job)
        self.assertIn("inputs.authorize_paid_api_call == true", paid_job)
        self.assertIn("github.ref == 'refs/heads/main'", paid_job)


if __name__ == "__main__":
    unittest.main()
