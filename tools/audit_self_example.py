#!/usr/bin/env python3
"""Keyless release-readiness checks for the repository self-example."""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

SCHEMA = "compiled-prose-source-audit/1"
SOURCES_HEADING = "## Sources identified for the essay"
SOURCE_ENTRY_RE = re.compile(r"^\*\*(.+?)\*\*\s*$", re.MULTILINE)
CITATION_GROUP_RE = re.compile(r"\[([^\]\n]*(?:19|20)\d{2}[^\]\n]*)\]")
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
BIB_ENTRY_RE = re.compile(r"^@\w+\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)
LATEX_CITE_RE = re.compile(
    r"\\(?:cite|parencite|textcite|autocite|footcite|smartcite|supercite|fullcite|"
    r"footfullcite|volcite|pvolcite|fvolcite|tvolcite|avolcite|citeauthor|citetitle|"
    r"citeyear|citedate|citeurl|nocite|citep|citet)\*?"
    r"(?:\s*\[[^\]]*\]){0,2}\s*\{([^{}]+)\}"
)
FAIL_SENTINEL = "@@FAIL"


@dataclass(frozen=True)
class AuditResult:
    source_keys: tuple[str, ...]
    cited_keys: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def _split_outline(text: str) -> tuple[str, str]:
    if SOURCES_HEADING not in text:
        raise ValueError(f"outline is missing required heading: {SOURCES_HEADING}")
    body, catalog = text.split(SOURCES_HEADING, 1)
    return body, catalog


def _citation_keys(text: str) -> set[str]:
    keys: set[str] = set()
    for match in CITATION_GROUP_RE.finditer(text):
        for raw in match.group(1).split(";"):
            key = raw.strip()
            if YEAR_RE.search(key):
                keys.add(key)
    return keys


def _catalog_keys(catalog: str) -> set[str]:
    return {match.group(1).strip() for match in SOURCE_ENTRY_RE.finditer(catalog)}


def _bib_keys(text: str) -> set[str]:
    return {match.group(1).strip() for match in BIB_ENTRY_RE.finditer(text)}


def _latex_citation_keys(text: str) -> set[str]:
    keys: set[str] = set()
    for match in LATEX_CITE_RE.finditer(text):
        keys.update(key.strip() for key in match.group(1).split(",") if key.strip())
    return keys


def _load_audit(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read source audit {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("source audit must be a JSON object")
    return data


def _valid_urls(values: object) -> bool:
    return (
        isinstance(values, list)
        and bool(values)
        and all(
            isinstance(value, str) and value.startswith(("https://", "http://"))
            for value in values
        )
    )


def audit(
    outline: Path,
    audit_path: Path,
    *,
    bibliography: Optional[Path] = None,
    final: Optional[Path] = None,
) -> AuditResult:
    text = outline.read_text(encoding="utf-8")
    body, catalog = _split_outline(text)
    cited = _citation_keys(body)
    catalogued = _catalog_keys(catalog)
    errors: list[str] = []

    missing_catalog = sorted(cited - catalogued)
    unused_catalog = sorted(catalogued - cited)
    if missing_catalog:
        errors.append("citations without catalog entries: " + ", ".join(missing_catalog))
    if unused_catalog:
        errors.append("catalog entries not cited by the essay: " + ", ".join(unused_catalog))

    data = _load_audit(audit_path)
    if data.get("schema") != SCHEMA:
        errors.append(f"source audit schema must be {SCHEMA!r}")
    if data.get("authoritative_source") != outline.name:
        errors.append(
            f"source audit authoritative_source must be {outline.name!r}, "
            f"got {data.get('authoritative_source')!r}"
        )
    verified_on = data.get("verified_on")
    if not isinstance(verified_on, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", verified_on) is None:
        errors.append("source audit must record verified_on as YYYY-MM-DD")

    records = data.get("sources")
    if not isinstance(records, list):
        errors.append("source audit sources must be a list")
        records = []

    by_key: dict[str, dict] = {}
    by_bib_key: dict[str, str] = {}
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"source audit record {index} is not an object")
            continue
        key = record.get("citation")
        if not isinstance(key, str) or not key:
            errors.append(f"source audit record {index} has no citation")
            continue
        if key in by_key:
            errors.append(f"duplicate source audit record: {key}")
            continue
        by_key[key] = record
        if record.get("metadata_status") != "verified":
            errors.append(f"{key}: metadata_status is not verified")
        if record.get("claim_support_status") != "verified":
            errors.append(f"{key}: claim_support_status is not verified")
        if not _valid_urls(record.get("checked_against")):
            errors.append(f"{key}: checked_against must contain at least one http(s) URL")

        bib_key = record.get("bib_key")
        if bibliography is not None:
            if not isinstance(bib_key, str) or not bib_key.strip():
                errors.append(f"{key}: bib_key is required when bibliography metadata is supplied")
            elif bib_key in by_bib_key:
                errors.append(
                    f"duplicate bibliography key {bib_key!r} for {by_bib_key[bib_key]!r} and {key!r}"
                )
            else:
                by_bib_key[bib_key] = key

    audit_keys = set(by_key)
    missing_audit = sorted(catalogued - audit_keys)
    extra_audit = sorted(audit_keys - catalogued)
    if missing_audit:
        errors.append("catalog entries without source-audit evidence: " + ", ".join(missing_audit))
    if extra_audit:
        errors.append("source-audit entries absent from catalog: " + ", ".join(extra_audit))

    bibliography_keys: set[str] = set()
    if bibliography is not None:
        bibliography_text = bibliography.read_text(encoding="utf-8")
        bibliography_keys = _bib_keys(bibliography_text)
        audit_bib_keys = set(by_bib_key)
        missing_bib = sorted(audit_bib_keys - bibliography_keys)
        extra_bib = sorted(bibliography_keys - audit_bib_keys)
        if missing_bib:
            errors.append("audited bibliography keys missing from .bib: " + ", ".join(missing_bib))
        if extra_bib:
            errors.append(".bib entries absent from source audit: " + ", ".join(extra_bib))

    if final is not None:
        final_text = final.read_text(encoding="utf-8")
        if FAIL_SENTINEL in final_text:
            errors.append("final artefact contains compiler failure sentinel")

        explicit_final = _citation_keys(final_text)
        unknown_labels = sorted(explicit_final - catalogued)
        if unknown_labels:
            errors.append(
                "final artefact contains non-authoritative explicit citation labels: "
                + ", ".join(unknown_labels)
            )

        if bibliography is not None:
            final_bib_keys = _latex_citation_keys(final_text)
            unknown_bib_keys = sorted(final_bib_keys - bibliography_keys)
            if unknown_bib_keys:
                errors.append(
                    "final artefact contains unknown bibliography citation keys: "
                    + ", ".join(unknown_bib_keys)
                )

            bib_filename = bibliography.name
            if final_bib_keys and f"\\addbibresource{{{bib_filename}}}" not in final_text:
                errors.append(
                    f"final artefact must bind formal citation commands to supplied bibliography {bib_filename!r}"
                )
            if "\\begin{thebibliography}" in final_text:
                errors.append(
                    "final artefact must not hand-render thebibliography when supplied bibliography metadata exists"
                )

    return AuditResult(
        source_keys=tuple(sorted(catalogued)),
        cited_keys=tuple(sorted(cited)),
        errors=tuple(errors),
    )


def _format_errors(errors: Iterable[str]) -> str:
    return "\n".join(f"- {error}" for error in errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outline", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--bibliography", type=Path)
    parser.add_argument("--final", type=Path)
    args = parser.parse_args()

    try:
        result = audit(
            args.outline,
            args.audit,
            bibliography=args.bibliography,
            final=args.final,
        )
    except (OSError, ValueError) as exc:
        print(f"self-example audit failed: {exc}", file=sys.stderr)
        return 2

    if not result.ok:
        print("self-example audit failed:\n" + _format_errors(result.errors), file=sys.stderr)
        return 2

    suffix = " and final mechanical citation checks" if args.final else ""
    print(f"self-example audit OK: {len(result.source_keys)} verified sources{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
