#!/usr/bin/env python3
import argparse
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List

STATUSES = ("PASS", "REVISE_REALISATION", "BLOCKED_SOURCE")
FINDING_RE = re.compile(
    r"^- \[(MAJOR|MINOR)\]\[(SOURCE|REALISATION|ADVISORY)\] (.+?) :: (.+)$"
)


class ReviewProtocolError(ValueError):
    pass


class SourceReviewBlocked(RuntimeError):
    pass


@dataclass(frozen=True)
class ReviewFinding:
    severity: str
    level: str
    location: str
    message: str


@dataclass(frozen=True)
class ReviewDecision:
    status: str
    findings: List[ReviewFinding]


def _unlink(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    temporary_path = Path(temporary)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(str(temporary_path), str(path))
    finally:
        _unlink(temporary_path)


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    temporary_path = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
        os.replace(str(temporary_path), str(path))
    finally:
        _unlink(temporary_path)


def parse_review(raw: str) -> ReviewDecision:
    """Parse the deliberately small peer-review machine protocol."""
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        raise ReviewProtocolError("review report is empty")

    status_lines = [line for line in lines if line.startswith("STATUS:")]
    if len(status_lines) != 1:
        raise ReviewProtocolError("review report must contain exactly one STATUS line")
    if lines[0] != status_lines[0]:
        raise ReviewProtocolError("STATUS must be the first non-empty line")

    prefix = "STATUS: "
    if not lines[0].startswith(prefix):
        raise ReviewProtocolError("STATUS line must use `STATUS: <value>`")
    status = lines[0][len(prefix) :]
    if status not in STATUSES:
        allowed = ", ".join(STATUSES)
        raise ReviewProtocolError(f"unknown review status `{status}`; expected one of: {allowed}")

    findings = []
    for line_number, line in enumerate(lines[1:], start=2):
        match = FINDING_RE.fullmatch(line)
        if match is None:
            raise ReviewProtocolError(
                "line "
                f"{line_number} is malformed; expected `- [MAJOR|MINOR]"
                "[SOURCE|REALISATION|ADVISORY] <location> :: <finding>`"
            )
        severity, level, location, message = match.groups()
        if not location.strip() or not message.strip():
            raise ReviewProtocolError(f"line {line_number} has an empty location or finding")
        findings.append(
            ReviewFinding(
                severity=severity,
                level=level,
                location=location.strip(),
                message=message.strip(),
            )
        )

    if any(finding.level == "SOURCE" for finding in findings):
        derived_status = "BLOCKED_SOURCE"
    elif any(finding.level == "REALISATION" for finding in findings):
        derived_status = "REVISE_REALISATION"
    else:
        derived_status = "PASS"

    if status != derived_status:
        raise ReviewProtocolError(
            f"declared status `{status}` conflicts with findings; expected `{derived_status}`"
        )

    return ReviewDecision(status=status, findings=findings)


def apply_review_decision(
    *,
    review: Path,
    realised: Path,
    final_output: Path,
    review_diagnostic: Path,
    final_diagnostic: Path,
) -> ReviewDecision:
    """Enforce review authority before any optional final-revision model call."""
    _unlink(final_output)
    _unlink(final_diagnostic)

    raw = review.read_text(encoding="utf-8")
    try:
        decision = parse_review(raw)
    except ReviewProtocolError as exc:
        _atomic_write(
            review_diagnostic,
            "# Review protocol error\n\n"
            f"{exc}. Compilation stopped before final revision.\n",
        )
        raise

    if decision.status == "BLOCKED_SOURCE":
        _atomic_write(
            review_diagnostic,
            "# Source revision required\n\n"
            "Peer review found source-level defects. Compilation stopped before final "
            "revision; the diagnostic review remains non-authoritative and must be "
            "resolved in the human-authored source.\n\n"
            + raw.rstrip()
            + "\n",
        )
        raise SourceReviewBlocked("peer review requires authorial source revision")

    _unlink(review_diagnostic)

    if decision.status == "PASS":
        _atomic_write_bytes(final_output, realised.read_bytes())

    return decision


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", required=True, type=Path)
    parser.add_argument("--realised", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--diagnostic", required=True, type=Path)
    parser.add_argument("--final-diagnostic", required=True, type=Path)
    args = parser.parse_args()

    try:
        decision = apply_review_decision(
            review=args.review,
            realised=args.realised,
            final_output=args.output,
            review_diagnostic=args.diagnostic,
            final_diagnostic=args.final_diagnostic,
        )
    except (ReviewProtocolError, SourceReviewBlocked) as exc:
        print(f"review: compilation blocked; {exc}; diagnostics: {args.diagnostic}", file=sys.stderr)
        return 2

    print(decision.status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
