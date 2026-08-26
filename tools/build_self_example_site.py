#!/usr/bin/env python3
"""Build the static GitHub Pages view of the repository's self-example."""

import argparse
import html
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


REQUIRED_ARTIFACTS = (
    "realise.tex",
    "peer_review.md",
    "final.tex",
    "final.pdf",
)

STYLE = """\
:root { color-scheme: light dark; }
html { font-family: Georgia, 'Times New Roman', serif; line-height: 1.6; }
body { max-width: 52rem; margin: 0 auto; padding: 2rem 1.25rem 5rem; }
nav, .build-info { font-family: system-ui, sans-serif; font-size: 0.9rem; }
nav { padding-bottom: 1rem; border-bottom: 1px solid #8886; margin-bottom: 2rem; }
nav a { margin-right: 1rem; }
.build-info { padding: 1rem; margin: 1rem 0 2rem; border: 1px solid #8886; border-radius: 0.4rem; }
code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
pre { overflow-x: auto; padding: 1rem; background: #8881; }
a { text-underline-offset: 0.15em; }
"""

ACCEPTANCE = """\
# Release acceptance review

This page is a **human semantic gate**, not a mechanically generated certificate of fidelity.
The mechanical gates establish source/provenance bookkeeping and protocol cleanliness and, once a
candidate has been generated, require a real LaTeX compilation. They cannot prove that generated
prose is a faithful target realisation of the authored conceptual source.

Before approving publication, compare `artifacts/final.tex` (or the rendered PDF) directly with
`artifacts/outline.md` and the selected target, and confirm all of the following:

- no material claim appears in the final text without authority in the outline;
- no represented authored proposition has been silently strengthened or weakened;
- no content-bearing example, theory, citation, attribution, or historical claim was invented downstream;
- the realised coverage matches the selected target: exhaustive targets retain all materially distinct source content, while any summarisation or omission is explicitly target-authorised;
- omitted material has not made retained material false, misleading, or detached from a necessary qualification, dependency, uncertainty, or context;
- evidence, attribution, and citation presentation matches the selected target without inventing or disguising support;
- where the target requires formal citations, required source-supplied citations remain attached to the claims they support;
- where the target explicitly suppresses formal citation apparatus, no formal citation syntax has leaked into the target-facing text and any necessary attribution is faithfully expressed in the target-appropriate form;
- peer review did not expand conceptual scope;
- the final peer-review report contains no unresolved source-level blocker;
- any generated illustrative scaffolding is faithful, traceable to a source-authorised concept, materially accurate, and removable without changing the work's claims or evidentiary support;
- the human-authored conceptual decisions remain inspectable separately from model realisation.

If any item fails, do **not** approve publication. Repair the authoritative source for source defects,
or the compiler/target layer for realisation defects, then recompile. Do not hand-patch conceptual
content into generated prose.

The source-verification evidence used for this candidate is retained as
`artifacts/source-audit.json`. Stable bibliographic/provenance metadata is retained separately as
`artifacts/references.bib`. Neither file adds conceptual authority beyond `outline.md` or requires
formal citation apparatus in a target that explicitly suppresses it.
"""


def _require_files(paths: Iterable[Path]) -> None:
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing publication inputs: " + ", ".join(missing))


def _run_pandoc(
    source: Path,
    output: Path,
    title: Optional[str],
    nav: Path,
    *,
    bibliography: Optional[Path] = None,
) -> None:
    command = [
        "pandoc",
        str(source),
        "--standalone",
        "--to=html5",
        "--mathjax",
    ]
    if bibliography is not None:
        command.extend(["--citeproc", f"--bibliography={bibliography}"])
    if title is not None:
        command.extend(["--metadata", f"title={title}"])
    command.extend(
        [
            "--css=style.css",
            "--include-before-body",
            str(nav),
            "-o",
            str(output),
        ]
    )
    subprocess.run(command, check=True)


def build_site(
    *,
    build_dir: Path,
    outline: Path,
    source_audit: Path,
    bibliography: Path,
    output_dir: Path,
    source_sha: str,
    model: str,
    target: str,
    run_url: str,
    target_id: Optional[str] = None,
    run_id: Optional[str] = None,
) -> None:
    artifacts = [build_dir / name for name in REQUIRED_ARTIFACTS]
    _require_files([outline, source_audit, bibliography, *artifacts])

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    raw_dir = output_dir / "artifacts"
    raw_dir.mkdir()

    for artifact in artifacts:
        shutil.copy2(artifact, raw_dir / artifact.name)
    shutil.copy2(outline, raw_dir / "outline.md")
    shutil.copy2(source_audit, raw_dir / "source-audit.json")
    shutil.copy2(bibliography, raw_dir / "references.bib")

    (output_dir / "style.css").write_text(STYLE, encoding="utf-8")
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    nav = output_dir / "_nav.html"
    safe_sha = html.escape(source_sha)
    safe_model = html.escape(model)
    safe_target = html.escape(target_id or target)
    safe_run_url = html.escape(run_url, quote=True)
    nav.write_text(
        "<nav>"
        '<a href="index.html">Final text</a>'
        '<a href="outline.html">Authoritative outline</a>'
        '<a href="peer-review.html">Peer review</a>'
        '<a href="acceptance.html">Acceptance review</a>'
        '<a href="artifacts/final.pdf">PDF</a>'
        '<a href="artifacts/final.tex">Raw LaTeX</a>'
        "</nav>"
        '<div class="build-info">'
        f"Source commit: <code>{safe_sha}</code><br>"
        f"Model: <code>{safe_model}</code><br>"
        f"Target: <code>{safe_target}</code><br>"
        f'<a href="{safe_run_url}">Compilation workflow run</a>'
        "</div>",
        encoding="utf-8",
    )

    # Bibliographic metadata remains available as provenance for every target.
    # Pandoc's native cite processor only renders formal references when the
    # generated target text actually contains citation commands.
    # Do not override final.tex metadata: its title must remain identical
    # between PDF and HTML renderings.
    _run_pandoc(
        build_dir / "final.tex",
        output_dir / "index.html",
        None,
        nav,
        bibliography=bibliography,
    )
    _run_pandoc(outline, output_dir / "outline.html", "Authoritative outline", nav)
    _run_pandoc(
        build_dir / "peer_review.md",
        output_dir / "peer-review.html",
        "Peer review diagnostic",
        nav,
    )
    acceptance_source = output_dir / "_acceptance.md"
    acceptance_source.write_text(ACCEPTANCE, encoding="utf-8")
    _run_pandoc(
        acceptance_source,
        output_dir / "acceptance.html",
        "Release acceptance review",
        nav,
    )
    acceptance_source.unlink()
    nav.unlink()

    metadata = {
        "source_sha": source_sha,
        "model": model,
        # Keep the legacy field for retained candidates produced before target IDs
        # were first-class metadata, while also recording the explicit layers.
        "target": target,
        "target_file": target,
        "workflow_run": run_url,
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifacts": list(REQUIRED_ARTIFACTS),
        "authoritative_source": "outline.md",
        "source_audit": "source-audit.json",
        "bibliography": "references.bib",
    }
    if target_id is not None:
        metadata["target_id"] = target_id
    if run_id is not None:
        metadata["workflow_run_id"] = run_id
    (output_dir / "build.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--outline", type=Path, required=True)
    parser.add_argument("--source-audit", type=Path, required=True)
    parser.add_argument("--bibliography", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--target-id")
    parser.add_argument("--run-url", required=True)
    parser.add_argument("--run-id")
    args = parser.parse_args()
    build_site(
        build_dir=args.build_dir,
        outline=args.outline,
        source_audit=args.source_audit,
        bibliography=args.bibliography,
        output_dir=args.output_dir,
        source_sha=args.source_sha,
        model=args.model,
        target=args.target,
        target_id=args.target_id,
        run_url=args.run_url,
        run_id=args.run_id,
    )


if __name__ == "__main__":
    main()
