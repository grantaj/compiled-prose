#!/usr/bin/env python3
import argparse
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

FAIL_SENTINEL = "@@FAIL"


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


def _failure_payload(raw: str) -> Optional[str]:
    first_line, separator, remainder = raw.partition("\n")
    if first_line.rstrip("\r") != FAIL_SENTINEL:
        return None
    return remainder if separator else ""


def _diagnostic(stage: str, message: str) -> str:
    return f"# Protocol error\n\nStage `{stage}` {message}\n"


def enforce_result(
    raw: str,
    *,
    stage: str,
    output: Path,
    diagnostic: Path,
) -> bool:
    """Publish exactly one stage result: a success artefact or a diagnostic."""
    _unlink(output)

    payload = _failure_payload(raw)
    if payload is not None:
        if not payload.strip():
            payload = _diagnostic(
                stage,
                "reported `@@FAIL` without any diagnostic detail.",
            )
        _atomic_write(diagnostic, payload)
        return False

    if not raw:
        _atomic_write(
            diagnostic,
            _diagnostic(
                stage,
                "returned empty output instead of a success artefact or `@@FAIL`.",
            ),
        )
        return False

    if raw.lstrip("\ufeff\r\n\t ").startswith(FAIL_SENTINEL):
        _atomic_write(
            diagnostic,
            _diagnostic(
                stage,
                "returned a failure sentinel with leading content; `@@FAIL` must be the first line.",
            ),
        )
        return False

    _unlink(diagnostic)
    _atomic_write(output, raw)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--diagnostic", required=True, type=Path)
    args = parser.parse_args()

    raw = sys.stdin.read()
    success = enforce_result(
        raw,
        stage=args.stage,
        output=args.output,
        diagnostic=args.diagnostic,
    )
    if success:
        return 0

    print(
        f"{args.stage}: compilation blocked; diagnostics: {args.diagnostic}",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
