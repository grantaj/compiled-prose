# Generated self-example site

`docs/` is the staging directory for the published self-example. The paid, approval-gated publication workflow regenerates this directory in its runner and deploys it with the GitHub Pages Actions deployment API. Generated prose is not committed back to the repository.

A successful compile produces an inspectable acceptance candidate before deployment. The candidate includes the authoritative outline, dated source-audit evidence, the verified `references.bib` rendering metadata, stage artefacts, final peer-review report, final LaTeX, a LaTeX-compiled PDF, model/source metadata, and a human source-authority acceptance checklist. The candidate is uploaded as a normal workflow artifact as well as the Pages artifact so it can be inspected while the `github-pages` environment is waiting for approval.

The paper PDF and HTML share the same bibliography metadata: LaTeX resolves `references.bib` through BibLaTeX/biber, and the Pages build passes that same file to Pandoc `--citeproc`. The HTML path does not maintain a second hand-written citation translation layer.

Configure GitHub Pages with **Source: GitHub Actions**, not branch-based `main / docs`. The authoritative essay source remains `outline.md`; the source-audit record and bibliography are evidence/rendering metadata about supplied references, and everything generated under `docs/` is downstream release evidence rather than conceptual authority.
