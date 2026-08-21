# Generated self-example site

`docs/` is the staging directory for the published self-example. The paid, approval-gated publication workflow regenerates this directory in its runner and deploys it with the GitHub Pages Actions deployment API. Generated prose is not committed back to the repository.

A successful compile produces an inspectable acceptance candidate before deployment. The candidate includes the authoritative outline, dated source-audit evidence, stage artefacts, final peer-review report, final LaTeX, a LaTeX-compiled PDF, model/source metadata, and a human source-authority acceptance checklist. The candidate is uploaded as a normal workflow artifact as well as the Pages artifact so it can be inspected while the `github-pages` environment is waiting for approval.

Configure GitHub Pages with **Source: GitHub Actions**, not branch-based `main / docs`. The authoritative essay source remains `outline.md`; the source-audit record is evidence about supplied references, and everything generated under `docs/` is downstream release evidence rather than conceptual authority.
