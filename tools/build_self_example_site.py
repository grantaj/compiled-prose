#!/usr/bin/env python3
"""Build the static GitHub Pages view of the repository's self-example."""

import argparse
import html
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


REQUIRED_ARTIFACTS = (
    "draft.tex",
    "smooth.tex",
    "revise.tex",
    "peer_review.md",
    "final.tex",
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


def _require_files(paths: Iterable[Path]) -> None:
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing publication inputs: " + ", ".join(missing))


def _run_pandoc(source: Path, output: Path, title: str, nav: Path) -> None:
    subprocess.run(
        [
            "pandoc",
            str(source),
            "--standalone",
            "--to=html5",
            "--mathjax",
            "--metadata",
            f"title={title}",
            "--css=style.css",
            "--include-before-body",
            str(nav),
            "-o",
            str(output),
        ],
        check=True,
    )


def build_site(
    *,
    build_dir: Path,
    outline: Path,
    output_dir: Path,
    source_sha: str,
    model: str,
    target: str,
    run_url: str,
) -> None:
    artifacts = [build_dir / name for name in REQUIRED_ARTIFACTS]
    _require_files([outline, *artifacts])

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    raw_dir = output_dir / "artifacts"
    raw_dir.mkdir()

    for artifact in artifacts:
        shutil.copy2(artifact, raw_dir / artifact.name)
    shutil.copy2(outline, raw_dir / "outline.md")

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

    _run_pandoc(
        build_dir / "final.tex",
        output_dir / "index.html",
        "Compiled Prose — self-example",
        nav,
    )
    _run_pandoc(outline, output_dir / "outline.html", "Authoritative outline", nav)
    _run_pandoc(
        build_dir / "peer_review.md",
        output_dir / "peer-review.html",
        "Peer review diagnostic",
        nav,
    )
    nav.unlink()

    metadata = {
        "source_sha": source_sha,
        "model": model,
        "target": target,
        "workflow_run": run_url,
        "published_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifacts": list(REQUIRED_ARTIFACTS),
    }
    (output_dir / "build.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--outline", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--run-url", required=True)
    args = parser.parse_args()
    build_site(
        build_dir=args.build_dir,
        outline=args.outline,
        output_dir=args.output_dir,
        source_sha=args.source_sha,
        model=args.model,
        target=args.target,
        run_url=args.run_url,
    )


if __name__ == "__main__":
    main()
