#!/usr/bin/env python3
"""Assemble a multi-target self-example Pages site from retained candidates."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urlparse

if __package__:
    from .build_self_example_site import ACCEPTANCE
    from .self_example_targets import TARGETS, TargetSpec, resolve_target
else:
    from build_self_example_site import ACCEPTANCE
    from self_example_targets import TARGETS, TargetSpec, resolve_target


REPOSITORY_URL = "https://github.com/grantaj/compiled-prose"
SHOWCASE_TITLE = "Compiled Prose self-example"

STYLE = """\
:root {
  color-scheme: light dark;
  --page: #f4f2ed;
  --surface: #fcfbf8;
  --ink: #17191e;
  --muted: #656a73;
  --line: #d7d3ca;
  --accent: #3d50d9;
  --accent-soft: #e8eaff;
  --code-bg: #ece9e2;
  --shadow: 0 12px 32px rgb(23 25 30 / 0.06);
}

@media (prefers-color-scheme: dark) {
  :root {
    --page: #15171b;
    --surface: #1d2026;
    --ink: #ececf0;
    --muted: #a7abb4;
    --line: #343841;
    --accent: #98a5ff;
    --accent-soft: #2a3158;
    --code-bg: #252932;
    --shadow: 0 14px 36px rgb(0 0 0 / 0.2);
  }
}

* { box-sizing: border-box; }
html {
  background: var(--page);
  color: var(--ink);
  font-family: ui-serif, Georgia, 'Times New Roman', serif;
  font-size: 17px;
  line-height: 1.65;
  text-rendering: optimizeLegibility;
}
body {
  max-width: 62rem;
  margin: 0 auto;
  padding: 2.25rem 1.5rem 6rem;
}
body > header { margin: 3.25rem 0 1.75rem; }
h1, h2, h3 {
  line-height: 1.14;
  letter-spacing: -0.025em;
}
h1 { font-size: clamp(2.25rem, 7vw, 4.35rem); margin: 0 0 1.4rem; }
h1.title { max-width: 13ch; }
h2 { font-size: 1.55rem; margin-top: 2.8rem; }
h3 { font-size: 1.15rem; margin-top: 2rem; }
p, li { max-width: 46rem; }
strong { font-weight: 700; }

nav, .build-info, .target-grid {
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem 0.35rem;
  align-items: center;
  padding: 0.4rem 0 1rem;
  border-bottom: 1px solid var(--line);
  margin-bottom: 2.4rem;
}
nav a {
  display: inline-block;
  color: var(--muted);
  border-radius: 0.35rem;
  padding: 0.35rem 0.5rem;
  font-size: 0.82rem;
  font-weight: 650;
  line-height: 1.25;
  text-decoration: none;
  white-space: nowrap;
}
nav a:hover, nav a:focus-visible {
  background: var(--accent-soft);
  color: var(--accent);
}
nav .repo-link {
  margin-left: auto;
  border: 1px solid var(--line);
  color: var(--ink);
  padding-inline: 0.7rem;
}

.build-info {
  background: var(--surface);
  border: 1px solid var(--line);
  border-left: 3px solid var(--accent);
  border-radius: 0.55rem;
  box-shadow: var(--shadow);
  color: var(--muted);
  font-size: 0.82rem;
  line-height: 1.65;
  padding: 0.9rem 1rem;
  margin: 1rem 0 2.6rem;
}
.build-info code { color: var(--ink); }
.build-info a { font-weight: 650; }

.target-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr));
  gap: 1rem;
  margin: 2.25rem 0;
}
.target-card {
  position: relative;
  overflow: hidden;
  min-height: 9rem;
  background: var(--surface);
  border: 1px solid var(--line);
  border-top: 3px solid var(--accent);
  border-radius: 0.6rem;
  box-shadow: var(--shadow);
  padding: 1.1rem 1.15rem 1.2rem;
  transition: transform 140ms ease, box-shadow 140ms ease;
}
.target-card:hover { transform: translateY(-2px); }
.target-card h2 {
  margin: 0 0 1.35rem;
  font-size: 1.05rem;
  letter-spacing: -0.01em;
}
.target-card h2 a { text-decoration: none; }
.target-card p {
  max-width: none;
  margin: 0;
  color: var(--muted);
  font-size: 0.8rem;
  line-height: 1.55;
}

code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
code {
  border-radius: 0.25rem;
  background: var(--code-bg);
  padding: 0.08em 0.28em;
  font-size: 0.88em;
}
pre {
  overflow-x: auto;
  background: var(--code-bg);
  border: 1px solid var(--line);
  border-radius: 0.5rem;
  padding: 1rem;
}
pre code { background: transparent; padding: 0; }
blockquote {
  margin-left: 0;
  border-left: 3px solid var(--line);
  padding-left: 1.1rem;
  color: var(--muted);
}
hr { border: 0; border-top: 1px solid var(--line); margin: 3rem 0; }
table { border-collapse: collapse; max-width: 100%; }
th, td { border-bottom: 1px solid var(--line); padding: 0.45rem 0.7rem; text-align: left; }
img { max-width: 100%; height: auto; }
a {
  color: var(--accent);
  text-decoration-thickness: 0.07em;
  text-underline-offset: 0.16em;
}
a:hover { text-decoration-thickness: 0.12em; }

@media (max-width: 42rem) {
  body { padding: 1.25rem 1rem 4rem; }
  nav .repo-link { margin-left: 0; }
  body > header { margin-top: 2.35rem; }
}

@media (prefers-reduced-motion: reduce) {
  .target-card { transition: none; }
  .target-card:hover { transform: none; }
}

@media print {
  :root { --page: #fff; --surface: #fff; --ink: #000; --muted: #444; --line: #bbb; }
  body { max-width: none; padding: 0; }
  nav { display: none; }
  .build-info, .target-card { box-shadow: none; }
}
"""

REQUIRED_RAW_ARTIFACTS = (
    "outline.md",
    "source-audit.json",
    "references.bib",
    "peer_review.md",
    "final.tex",
    "final.pdf",
)


@dataclass(frozen=True)
class Candidate:
    spec: TargetSpec
    root: Path
    metadata: dict[str, object]
    workflow_run_id: str
    outline_bytes: bytes
    outline_sha256: str

    @property
    def artifacts(self) -> Path:
        return self.root / "artifacts"


def _require_files(paths: Iterable[Path]) -> None:
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing candidate inputs: " + ", ".join(missing))


def locate_candidate(root: Path) -> Path:
    """Resolve an artifact-download directory to exactly one candidate root."""
    direct = root / "build.json"
    if direct.is_file():
        return root
    matches = sorted(path.parent for path in root.rglob("build.json"))
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one retained candidate under {root}, found {len(matches)}"
        )
    return matches[0]


def locate_showcase(root: Path) -> Path:
    """Resolve an artifact-download directory to exactly one prior showcase root."""
    direct = root / "showcase.json"
    if direct.is_file():
        return root
    matches = sorted(path.parent for path in root.rglob("showcase.json"))
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one retained showcase under {root}, found {len(matches)}"
        )
    return matches[0]


def _run_id_from_url(run_url: str) -> Optional[str]:
    parts = [part for part in urlparse(run_url).path.split("/") if part]
    for index in range(len(parts) - 2):
        if parts[index : index + 2] == ["actions", "runs"]:
            value = parts[index + 2]
            return value if value.isdigit() else None
    return None


def _candidate_run_id(identifier: str, metadata: dict[str, object]) -> str:
    run_url = metadata.get("workflow_run")
    if not isinstance(run_url, str) or not run_url:
        raise ValueError(f"candidate for {identifier} has no usable 'workflow_run' metadata")

    url_run_id = _run_id_from_url(run_url)
    declared = metadata.get("workflow_run_id")
    if declared is not None:
        if not isinstance(declared, str) or not declared.isdigit():
            raise ValueError(
                f"candidate for {identifier} has invalid 'workflow_run_id' metadata"
            )
        if url_run_id is not None and declared != url_run_id:
            raise ValueError(
                f"candidate for {identifier} has inconsistent workflow run provenance: "
                f"id={declared}, url={url_run_id}"
            )
        return declared

    if url_run_id is None:
        raise ValueError(
            f"candidate for {identifier} has no recoverable workflow run ID"
        )
    return url_run_id


def load_candidate(
    identifier: str,
    root: Path,
    *,
    expected_run_id: Optional[str] = None,
) -> Candidate:
    spec = resolve_target(identifier)
    candidate_root = locate_candidate(root)
    build_json = candidate_root / "build.json"
    artifacts = candidate_root / "artifacts"
    _require_files([build_json, *(artifacts / name for name in REQUIRED_RAW_ARTIFACTS)])

    metadata = json.loads(build_json.read_text(encoding="utf-8"))
    actual_target_id = metadata.get("target_id")
    actual_target_file = metadata.get("target_file", metadata.get("target"))
    if actual_target_id is None and actual_target_file is None:
        raise ValueError(f"candidate for {identifier} has no target metadata")
    if actual_target_id is not None and actual_target_id != identifier:
        raise ValueError(
            f"candidate for {identifier} reports target ID {actual_target_id!r}, "
            f"expected {identifier!r}"
        )
    if actual_target_file is not None and actual_target_file != spec.path:
        raise ValueError(
            f"candidate for {identifier} reports target file {actual_target_file!r}, "
            f"expected {spec.path!r}"
        )
    for field in ("model", "source_sha"):
        if not isinstance(metadata.get(field), str) or not metadata[field]:
            raise ValueError(f"candidate for {identifier} has no usable {field!r} metadata")

    workflow_run_id = _candidate_run_id(identifier, metadata)
    if expected_run_id is not None:
        if not expected_run_id.isdigit():
            raise ValueError(f"expected workflow run ID for {identifier} must be numeric")
        if workflow_run_id != expected_run_id:
            raise ValueError(
                f"candidate for {identifier} came from workflow run {workflow_run_id}, "
                f"but run {expected_run_id} was selected"
            )

    outline_bytes = (artifacts / "outline.md").read_bytes()
    return Candidate(
        spec=spec,
        root=candidate_root,
        metadata=metadata,
        workflow_run_id=workflow_run_id,
        outline_bytes=outline_bytes,
        outline_sha256=hashlib.sha256(outline_bytes).hexdigest(),
    )


def _run_pandoc(
    source: Path,
    output: Path,
    *,
    css: str,
    nav: Path,
    title: Optional[str] = None,
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
            f"--css={css}",
            "--include-before-body",
            str(nav),
            "-o",
            str(output),
        ]
    )
    subprocess.run(command, check=True)


def _nav_html(candidates: list[Candidate], *, prefix: str, info: str = "") -> str:
    links = [
        f'<a href="{prefix}index.html">Showcase</a>',
        f'<a href="{prefix}outline.html">Authoritative outline</a>',
    ]
    for candidate in candidates:
        links.append(
            f'<a href="{prefix}targets/{candidate.spec.identifier}/index.html">'
            f"{html.escape(candidate.spec.label)}</a>"
        )
    links.append(
        f'<a class="repo-link" href="{REPOSITORY_URL}">GitHub repository ↗</a>'
    )
    block = "<nav>" + "".join(links) + "</nav>"
    if info:
        block += f'<div class="build-info">{info}</div>'
    return block


def _candidate_info(candidate: Candidate) -> str:
    metadata = candidate.metadata
    run_url = html.escape(str(metadata["workflow_run"]), quote=True)
    return (
        f"Target: <code>{html.escape(candidate.spec.identifier)}</code><br>"
        f"Model: <code>{html.escape(str(metadata['model']))}</code><br>"
        f"Compilation commit: <code>{html.escape(str(metadata['source_sha']))}</code><br>"
        f"Compilation run: <code>{candidate.workflow_run_id}</code><br>"
        f"Authoritative outline SHA-256: <code>{candidate.outline_sha256}</code><br>"
        f'<a href="{run_url}">Compilation workflow run</a> · '
        '<a href="peer-review.html">Peer review</a> · '
        '<a href="acceptance.html">Acceptance review</a> · '
        '<a href="artifacts/final.pdf">PDF</a> · '
        '<a href="artifacts/final.tex">Raw LaTeX</a>'
    )


def _landing_markdown(candidates: list[Candidate]) -> str:
    cards = []
    for candidate in candidates:
        cards.append(
            '<div class="target-card">'
            f"<h2><a href=\"targets/{candidate.spec.identifier}/index.html\">"
            f"{html.escape(candidate.spec.label)}</a></h2>"
            f"<p><code>{candidate.spec.identifier}</code><br>"
            f"Model: <code>{html.escape(str(candidate.metadata['model']))}</code></p>"
            "</div>"
        )
    return (
        "This showcase holds the authored argument fixed and compiles it for different "
        "audiences and genres. The **authoritative outline** is the conceptual source; the "
        "target renderings are derived realisations, not progressively better versions of the "
        "essay.\n\n"
        '<div class="target-grid">\n'
        + "\n".join(cards)
        + "\n</div>\n\n"
        "Start with the [authoritative outline](outline.html), then compare the target renderings. "
        f"The compiler, prompts, and source for this example are in the [GitHub repository]({REPOSITORY_URL}).\n"
    )


def build_showcase(
    *,
    candidate_roots: dict[str, Path],
    output_dir: Path,
    base_showcase: Optional[Path] = None,
    expected_outline: Optional[Path] = None,
    candidate_run_ids: Optional[dict[str, str]] = None,
) -> None:
    unknown = set(candidate_roots) - set(TARGETS)
    if unknown:
        raise ValueError("unsupported target(s): " + ", ".join(sorted(unknown)))
    if candidate_run_ids is not None:
        unknown_runs = set(candidate_run_ids) - set(candidate_roots)
        if unknown_runs:
            raise ValueError(
                "workflow run IDs supplied for non-selected target(s): "
                + ", ".join(sorted(unknown_runs))
            )

    selected_roots: dict[str, Path] = {}
    if base_showcase is not None:
        base_root = locate_showcase(base_showcase)
        manifest = json.loads((base_root / "showcase.json").read_text(encoding="utf-8"))
        if manifest.get("schema") != "compiled-prose-self-example-showcase/1":
            raise ValueError("unsupported retained showcase schema")
        base_targets = manifest.get("targets")
        if not isinstance(base_targets, dict) or not base_targets:
            raise ValueError("retained showcase has no target manifest")
        unknown_base = set(base_targets) - set(TARGETS)
        if unknown_base:
            raise ValueError(
                "retained showcase contains unsupported target(s): "
                + ", ".join(sorted(unknown_base))
            )
        for identifier in base_targets:
            selected_roots[identifier] = base_root / "targets" / identifier

    # Explicit candidates add missing targets or deliberately replace the same
    # target from the retained base. Unmentioned base targets are preserved.
    selected_roots.update(candidate_roots)
    if not selected_roots:
        raise ValueError("at least one retained self-example candidate is required")
    if "journal_academic" not in selected_roots:
        raise ValueError(
            "journal_academic must remain in every published showcase so the "
            "existing top-level academic evidence URLs stay valid"
        )

    candidates = [
        load_candidate(
            identifier,
            selected_roots[identifier],
            expected_run_id=(candidate_run_ids or {}).get(identifier)
            if identifier in candidate_roots
            else None,
        )
        for identifier in TARGETS
        if identifier in selected_roots
    ]
    authoritative_digest = candidates[0].outline_sha256
    if expected_outline is not None:
        _require_files([expected_outline])
        expected_bytes = expected_outline.read_bytes()
        if candidates[0].outline_bytes != expected_bytes:
            expected_digest = hashlib.sha256(expected_bytes).hexdigest()
            raise ValueError(
                "candidate authoritative outline differs from current source: "
                f"candidate={authoritative_digest}, current={expected_digest}"
            )
    for candidate in candidates[1:]:
        if candidate.outline_bytes != candidates[0].outline_bytes:
            raise ValueError(
                "candidate authoritative outlines differ: "
                f"{candidates[0].spec.identifier}={authoritative_digest}, "
                f"{candidate.spec.identifier}={candidate.outline_sha256}"
            )

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    (output_dir / "targets").mkdir()
    (output_dir / "artifacts").mkdir()
    (output_dir / "style.css").write_text(STYLE, encoding="utf-8")
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")
    (output_dir / "artifacts" / "outline.md").write_bytes(candidates[0].outline_bytes)

    root_info = (
        "All renderings on this page use the same authoritative outline. "
        "Targets are audience/genre contracts, not quality levels.<br>"
        f"Authoritative outline SHA-256: <code>{authoritative_digest}</code>"
    )
    root_nav = output_dir / "_nav.html"
    root_nav.write_text(_nav_html(candidates, prefix="", info=root_info), encoding="utf-8")

    landing = output_dir / "_index.md"
    landing.write_text(_landing_markdown(candidates), encoding="utf-8")
    _run_pandoc(
        landing,
        output_dir / "index.html",
        css="style.css",
        nav=root_nav,
        title=SHOWCASE_TITLE,
    )
    _run_pandoc(
        candidates[0].artifacts / "outline.md",
        output_dir / "outline.html",
        css="style.css",
        nav=root_nav,
        title="Authoritative outline",
    )

    # Every published showcase includes the academic target so these legacy URLs
    # are guaranteed rather than opportunistic compatibility views.
    journal = next(
        candidate for candidate in candidates if candidate.spec.identifier == "journal_academic"
    )
    shutil.copytree(journal.artifacts, output_dir / "artifacts", dirs_exist_ok=True)
    journal_root_nav = output_dir / "_journal_nav.html"
    journal_root_nav.write_text(
        _nav_html(candidates, prefix="", info=_candidate_info(journal)),
        encoding="utf-8",
    )
    _run_pandoc(
        journal.artifacts / "peer_review.md",
        output_dir / "peer-review.html",
        css="style.css",
        nav=journal_root_nav,
        title="Academic journal: peer review",
    )
    root_acceptance = output_dir / "_acceptance.md"
    root_acceptance.write_text(ACCEPTANCE, encoding="utf-8")
    _run_pandoc(
        root_acceptance,
        output_dir / "acceptance.html",
        css="style.css",
        nav=journal_root_nav,
        title="Academic journal: release acceptance review",
    )
    root_acceptance.unlink()
    journal_root_nav.unlink()

    landing.unlink()
    root_nav.unlink()

    manifest_targets: dict[str, object] = {}
    for candidate in candidates:
        target_dir = output_dir / "targets" / candidate.spec.identifier
        target_dir.mkdir(parents=True)
        shutil.copytree(candidate.artifacts, target_dir / "artifacts")
        shutil.copy2(candidate.root / "build.json", target_dir / "build.json")

        nav = target_dir / "_nav.html"
        nav.write_text(
            _nav_html(candidates, prefix="../../", info=_candidate_info(candidate)),
            encoding="utf-8",
        )
        _run_pandoc(
            candidate.artifacts / "final.tex",
            target_dir / "index.html",
            css="../../style.css",
            nav=nav,
            bibliography=candidate.artifacts / "references.bib",
        )
        _run_pandoc(
            candidate.artifacts / "peer_review.md",
            target_dir / "peer-review.html",
            css="../../style.css",
            nav=nav,
            title=f"{candidate.spec.label}: peer review",
        )
        acceptance = target_dir / "_acceptance.md"
        acceptance.write_text(ACCEPTANCE, encoding="utf-8")
        _run_pandoc(
            acceptance,
            target_dir / "acceptance.html",
            css="../../style.css",
            nav=nav,
            title=f"{candidate.spec.label}: release acceptance review",
        )
        acceptance.unlink()
        nav.unlink()

        manifest_targets[candidate.spec.identifier] = {
            "label": candidate.spec.label,
            "target_file": candidate.spec.path,
            "model": candidate.metadata["model"],
            "compilation_commit": candidate.metadata["source_sha"],
            "workflow_run": candidate.metadata["workflow_run"],
            "workflow_run_id": candidate.workflow_run_id,
            "candidate_build": f"targets/{candidate.spec.identifier}/build.json",
        }

    manifest = {
        "schema": "compiled-prose-self-example-showcase/1",
        "authoritative_source": "outline.md",
        "authoritative_outline_sha256": authoritative_digest,
        "targets": manifest_targets,
    }
    (output_dir / "showcase.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _parse_candidate(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("candidate must be TARGET=PATH")
    identifier, path = value.split("=", 1)
    try:
        resolve_target(identifier)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    if not path:
        raise argparse.ArgumentTypeError("candidate path must not be empty")
    return identifier, Path(path)


def _parse_run_id(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("candidate run ID must be TARGET=RUN_ID")
    identifier, run_id = value.split("=", 1)
    try:
        resolve_target(identifier)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    if not run_id.isdigit():
        raise argparse.ArgumentTypeError("candidate workflow run ID must be numeric")
    return identifier, run_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--candidate",
        action="append",
        default=[],
        type=_parse_candidate,
        metavar="TARGET=PATH",
    )
    parser.add_argument(
        "--candidate-run-id",
        action="append",
        default=[],
        type=_parse_run_id,
        metavar="TARGET=RUN_ID",
    )
    parser.add_argument("--base-showcase", type=Path)
    parser.add_argument("--expected-outline", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    candidate_roots: dict[str, Path] = {}
    for identifier, path in args.candidate:
        if identifier in candidate_roots:
            parser.error(f"candidate target supplied more than once: {identifier}")
        candidate_roots[identifier] = path
    candidate_run_ids: dict[str, str] = {}
    for identifier, run_id in args.candidate_run_id:
        if identifier in candidate_run_ids:
            parser.error(f"candidate workflow run ID supplied more than once: {identifier}")
        candidate_run_ids[identifier] = run_id
    if set(candidate_run_ids) != set(candidate_roots):
        parser.error("every explicit candidate must have exactly one --candidate-run-id")
    build_showcase(
        candidate_roots=candidate_roots,
        candidate_run_ids=candidate_run_ids,
        output_dir=args.output_dir,
        base_showcase=args.base_showcase,
        expected_outline=args.expected_outline,
    )


if __name__ == "__main__":
    main()
