#!/usr/bin/env python3
"""Build the static GitHub Pages view of the repository's self-example."""

import argparse
import html
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


REQUIRED_ARTIFACTS = (
    "draft.tex",
    "smooth.tex",
    "revise.tex",
    "peer_review.md",
    "final.tex",
    "final.pdf",
)

_BIBLIOGRAPHY_RE = re.compile(
    r"\\begin\{thebibliography\}\{[^{}]*\}(.*?)\\end\{thebibliography\}",
    re.DOTALL,
)
_BIBITEM_RE = re.compile(
    r"\\bibitem(?:\[(?P<label>[^\]]+)\])?\{(?P<key>[^{}]+)\}"
)
_SIMPLE_CITE_RE = re.compile(r"\\cite\s*\{(?P<keys>[^{}]+)\}")
_ANY_CITE_RE = re.compile(r"\\cite[a-zA-Z*]*\s*(?:\[|\{)")

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
The mechanical gates establish source/citation bookkeeping and protocol cleanliness and, once a
candidate has been generated, require a real LaTeX compilation. They cannot prove that generated
prose is materially equivalent to the authored conceptual source.

Before approving publication, compare `artifacts/final.tex` (or the rendered PDF) directly with
`artifacts/outline.md` and confirm all of the following:

- no material claim appears in the final essay without authority in the outline;
- no authored proposition has been silently strengthened or weakened;
- no example, theory, citation, or historical claim was introduced downstream;
- every source-supplied citation remains present and attached to the claim it supports;
- peer review did not expand conceptual scope;
- material qualifications, uncertainty, exclusions, and domain boundaries are preserved;
- the final peer-review report contains no unresolved source-level blocker;
- the human-authored conceptual decisions remain inspectable separately from model realisation.

If any item fails, do **not** approve publication. Repair the authoritative source for source defects,
or the compiler/prompt layer for compiler defects, then recompile. Do not hand-patch conceptual
content into generated prose.

The source-verification evidence used for this candidate is retained as
`artifacts/source-audit.json`. It records audit evidence only and is not an additional conceptual
authority for the compiler.
"""


def _require_files(paths: Iterable[Path]) -> None:
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing publication inputs: " + ", ".join(missing))


def _prepare_final_tex_for_html(source: Path, output: Path) -> None:
    """Make Pandoc's HTML view preserve embedded LaTeX citation semantics.

    Pandoc can read ``thebibliography`` text but, without separate structured
    bibliography data, emits empty spans for ``\\cite{...}`` and may collapse
    adjacent ``\\bibitem`` entries.  The validated LaTeX/PDF remains canonical;
    this creates only a temporary HTML-rendering copy with explicit linked
    citation labels and reference entries.
    """

    tex = source.read_text(encoding="utf-8")
    bibliography_matches = list(_BIBLIOGRAPHY_RE.finditer(tex))

    if not bibliography_matches:
        if _ANY_CITE_RE.search(tex):
            raise ValueError(
                "HTML rendering found LaTeX citations without an embedded "
                "thebibliography environment"
            )
        output.write_text(tex, encoding="utf-8")
        return

    if len(bibliography_matches) != 1:
        raise ValueError("HTML rendering supports exactly one thebibliography environment")

    bibliography = bibliography_matches[0]
    body = bibliography.group(1)
    item_matches = list(_BIBITEM_RE.finditer(body))
    if not item_matches:
        raise ValueError("thebibliography contains no bibitem entries")

    entries = []
    by_key = {}
    for index, item in enumerate(item_matches, start=1):
        key = item.group("key").strip()
        if not key:
            raise ValueError("thebibliography contains an empty bibitem key")
        if key in by_key:
            raise ValueError(f"duplicate bibitem key: {key}")

        next_start = (
            item_matches[index].start() if index < len(item_matches) else len(body)
        )
        reference = body[item.end() : next_start].strip()
        if not reference:
            raise ValueError(f"bibitem has no reference text: {key}")

        label = (item.group("label") or str(index)).strip()
        entries.append((key, label, reference))
        by_key[key] = (index, label)

    def replace_cite(match: re.Match) -> str:
        keys = [key.strip() for key in match.group("keys").split(",")]
        if not keys or any(not key for key in keys):
            raise ValueError("empty citation key in final LaTeX")

        links = []
        for key in keys:
            if key not in by_key:
                raise ValueError(f"citation key has no bibitem: {key}")
            number, label = by_key[key]
            links.append(f"\\href{{#ref-{number}}}{{[{label}]}}")
        return ", ".join(links)

    converted = _SIMPLE_CITE_RE.sub(replace_cite, tex)
    if _ANY_CITE_RE.search(converted):
        raise ValueError(
            "HTML rendering encountered an unsupported LaTeX citation command; "
            "only simple \\cite{...} is supported"
        )

    references = ["\\section*{References}", "\\begin{description}"]
    for number, (_, label, reference) in enumerate(entries, start=1):
        references.append(
            f"\\item[{{[{label}]}}] \\hypertarget{{ref-{number}}}{{}} {reference}"
        )
    references.append("\\end{description}")
    rendered_bibliography = "\n".join(references)

    converted = (
        converted[: bibliography.start()]
        + rendered_bibliography
        + converted[bibliography.end() :]
    )
    output.write_text(converted, encoding="utf-8")


def _run_pandoc(
    source: Path, output: Path, title: Optional[str], nav: Path
) -> None:
    command = [
        "pandoc",
        str(source),
        "--standalone",
        "--to=html5",
        "--mathjax",
    ]
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
    output_dir: Path,
    source_sha: str,
    model: str,
    target: str,
    run_url: str,
) -> None:
    artifacts = [build_dir / name for name in REQUIRED_ARTIFACTS]
    _require_files([outline, source_audit, *artifacts])

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    raw_dir = output_dir / "artifacts"
    raw_dir.mkdir()

    for artifact in artifacts:
        shutil.copy2(artifact, raw_dir / artifact.name)
    shutil.copy2(outline, raw_dir / "outline.md")
    shutil.copy2(source_audit, raw_dir / "source-audit.json")

    (output_dir / "style.css").write_text(STYLE, encoding="utf-8")
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    nav = output_dir / "_nav.html"
    safe_sha = html.escape(source_sha)
    safe_model = html.escape(model)
    safe_target = html.escape(target)
    safe_run_url = html.escape(run_url, quote=True)
    nav.write_text(
        "<nav>"
        '<a href="index.html">Final essay</a>'
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

    final_html_source = output_dir / "_final_for_html.tex"
    _prepare_final_tex_for_html(build_dir / "final.tex", final_html_source)
    try:
        # Do not override final.tex metadata: its authored/generated paper title
        # must be the same title readers see in both the PDF and HTML views.
        _run_pandoc(final_html_source, output_dir / "index.html", None, nav)
    finally:
        final_html_source.unlink(missing_ok=True)

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
        "target": target,
        "workflow_run": run_url,
        "published_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifacts": list(REQUIRED_ARTIFACTS),
        "authoritative_source": "outline.md",
        "source_audit": "source-audit.json",
    }
    (output_dir / "build.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--outline", type=Path, required=True)
    parser.add_argument("--source-audit", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--run-url", required=True)
    args = parser.parse_args()
    build_site(
        build_dir=args.build_dir,
        outline=args.outline,
        source_audit=args.source_audit,
        output_dir=args.output_dir,
        source_sha=args.source_sha,
        model=args.model,
        target=args.target,
        run_url=args.run_url,
    )


if __name__ == "__main__":
    main()
