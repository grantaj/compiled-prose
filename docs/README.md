# Generated self-example site

`docs/` is only a repository placeholder/staging location; generated prose is not committed back to the source tree. The public self-example is assembled and deployed by GitHub Pages Actions from retained candidate artifacts.

Self-example release now has two deliberately separate workflows:

1. **Compile self-example target** is the only provider-capable workflow. It is manual, approval-gated, compiles exactly one selected target, and uploads a retained candidate artifact. It does **not** publish Pages.
2. **Publish self-example** is strictly keyless. It accepts explicit compilation run IDs, downloads those retained candidates, verifies that they contain the same authoritative `outline.md`, assembles the multi-target site, and deploys the selected artifacts. It never recompiles an existing artifact.

The initial public target set is `journal_academic`, `magazine_general`, and `explain_like_im_5`. The Pages landing page presents these as audience/genre contracts rather than quality levels, and renders the authoritative outline as a first-class view so readers can compare the authored source directly with each realization.

A successful compile candidate includes the authoritative outline, dated source-audit evidence, the verified `references.bib` rendering metadata, stage artifacts, final peer-review report, final LaTeX, a LaTeX-compiled PDF, model/source metadata, and a human source-authority acceptance checklist. Candidate artifacts are retained independently of Pages so a later publish can reuse them without making another model call.

The publish assembler compares the exact authoritative outline bytes across selected candidates. Compiler repository commits may differ: that is intentional so an already-accepted rendering can be reused after workflow or publication code changes, provided the authored outline itself is unchanged. Each target keeps its own compilation commit/model/run provenance in the published site.

The paper PDF and HTML share the same bibliography metadata: LaTeX resolves `references.bib` through BibLaTeX/biber, and the Pages build passes that same file to Pandoc `--citeproc`. The HTML path does not maintain a second hand-written citation translation layer.

Configure GitHub Pages with **Source: GitHub Actions**, not branch-based `main / docs`. The authoritative essay source remains `outline.md`; the source-audit record and bibliography are evidence/rendering metadata about supplied references, and everything generated for Pages is downstream release evidence rather than conceptual authority.
