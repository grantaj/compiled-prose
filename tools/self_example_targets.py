#!/usr/bin/env python3
"""Canonical public target identifiers for the self-example workflows."""

from __future__ import annotations

import argparse
from dataclasses import dataclass


@dataclass(frozen=True)
class TargetSpec:
    identifier: str
    path: str
    label: str
    citation_audit: str


TARGETS = {
    "journal_academic": TargetSpec(
        identifier="journal_academic",
        path="prompts/targets/journal_academic.md",
        label="Academic journal",
        citation_audit="all_source",
    ),
    "magazine_general": TargetSpec(
        identifier="magazine_general",
        path="prompts/targets/magazine_general.md",
        label="General-interest essay",
        citation_audit="all_source",
    ),
    "explain_like_im_5": TargetSpec(
        identifier="explain_like_im_5",
        path="prompts/targets/explain_like_im_5.md",
        label="Explain for a five-year-old",
        citation_audit="known_only",
    ),
}


def resolve_target(identifier: str) -> TargetSpec:
    try:
        return TARGETS[identifier]
    except KeyError as exc:
        allowed = ", ".join(TARGETS)
        raise ValueError(
            f"unsupported self-example target {identifier!r}; allowed: {allowed}"
        ) from exc


def resolve_target_path(path: str) -> TargetSpec:
    matches = [spec for spec in TARGETS.values() if spec.path == path]
    if len(matches) == 1:
        return matches[0]
    allowed = ", ".join(spec.path for spec in TARGETS.values())
    raise ValueError(f"unsupported self-example target path {path!r}; allowed: {allowed}")


def main() -> None:
    parser = argparse.ArgumentParser()
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("identifier", nargs="?")
    selector.add_argument("--path")
    parser.add_argument(
        "--field",
        choices=("path", "label", "identifier", "citation_audit"),
        default="path",
    )
    args = parser.parse_args()
    try:
        spec = resolve_target_path(args.path) if args.path else resolve_target(args.identifier)
    except ValueError as exc:
        parser.error(str(exc))
    print(getattr(spec, args.field))


if __name__ == "__main__":
    main()
