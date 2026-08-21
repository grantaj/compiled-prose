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


STYLE = """\
:root { color-scheme: light dark; }
html { font-family: Georgia, 'Times New Roman', serif; line-height: 1.6; }
body { max-width: 58rem; margin: 0 auto; padding: 2rem 1.25rem 5rem; }
nav, .build-info, .target-grid { font-family: system-ui, sans-serif; }
nav { padding-bottom: 1rem; border-bottom: 1px solid #8886; margin-bottom: 2rem; }
nav a { margin-right: 1rem; white-space: nowrap; }
.build-info { font-size: 0.9rem; padding: 1rem; margin: 1rem 0 2rem; border: 1px solid #8886; border-radius: 0.4rem; }
.target-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: 1rem; margin: 2rem 0; }
.target-card { border: 1px solid #8886; border-radius: 0.4rem; padding: 1rem; }
.target-card h2 { margin-top: 0; font-size: 1.05rem; }
code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
pre { overflow-x: auto; padding: 1rem; background: #8881; }
a { text-underline-offset: 0.15em; }
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
    landing = output_dir / "_index.md"
    landing.write_text(
        "# Compiled Prose self-example\n\n"
        "This showcase holds the authored argument fixed and compiles it for different "
        "audiences and genres. The **authoritative outline** is the conceptual source; the "
        "target renderings are derived realisations, not progressively better versions of the "
        "essay.\n\n"
        '<div class="target-grid">\n'
        + "\n".join(cards)
        + "\n</div>\n\n"
        "Start with the [authoritative outline](outline.html), then compare the target renderings.\n",
        encoding="utf-8",
    )
    _run_pandoc(
        landing,
        output_dir / "index.html",
        css="style.css",
        nav=root_nav,
        title="Compiled Prose self-example",
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
