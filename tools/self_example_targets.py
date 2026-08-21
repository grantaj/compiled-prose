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


TARGETS = {
    "journal_academic": TargetSpec(
        identifier="journal_academic",
        path="prompts/targets/journal_academic.md",
        label="Academic journal",
    ),
    "magazine_general": TargetSpec(
        identifier="magazine_general",
        path="prompts/targets/magazine_general.md",
        label="General-interest essay",
    ),
    "explain_like_im_5": TargetSpec(
        identifier="explain_like_im_5",
        path="prompts/targets/explain_like_im_5.md",
        label="Explain for a non-specialist",
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("identifier")
    parser.add_argument(
        "--field",
        choices=("path", "label", "identifier"),
        default="path",
    )
    args = parser.parse_args()
    try:
        spec = resolve_target(args.identifier)
    except ValueError as exc:
        parser.error(str(exc))
    print(getattr(spec, args.field))


if __name__ == "__main__":
    main()
