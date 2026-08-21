#!/usr/bin/env python3
import argparse
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

FAIL_SENTINEL = "@@FAIL"
OUTPUT_TYPES = ("tex", "md")


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


def _complete_tex_document(raw: str) -> bool:
    content = raw.lstrip("\ufeff")
    if not content.startswith("\\documentclass"):
        return False

    begin = content.find("\\begin{document}")
    end = content.rfind("\\end{document}")
    if begin < 0 or end < begin:
        return False

    tail = content[end + len("\\end{document}") :]
    return not tail.strip()


def _success_protocol_error(raw: str, output_type: str) -> Optional[str]:
    if any(line.strip() == FAIL_SENTINEL for line in raw.splitlines()):
        return "mixed the `@@FAIL` failure sentinel into a nominal success artefact."

    if output_type == "tex":
        if not _complete_tex_document(raw):
            return (
                "returned content that is not a complete raw LaTeX document; "
                "expected `\\documentclass`, an ordered `\\begin{document}` / "
                "`\\end{document}`, and no trailing content."
            )
        return None

    if output_type == "md":
        if _complete_tex_document(raw):
            return "returned a complete LaTeX document where Markdown was declared."
        return None

    return f"declared unsupported output type `{output_type}`."


def _write_protocol_failure(stage: str, diagnostic: Path, message: str) -> None:
    _atomic_write(diagnostic, _diagnostic(stage, message))


def enforce_result(
    raw: str,
    *,
    stage: str,
    output_type: str,
    output: Path,
    diagnostic: Path,
) -> bool:
    """Publish exactly one stage result: a valid success artefact or a diagnostic."""
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

    if not raw.strip("\ufeff\r\n\t "):
        _write_protocol_failure(
            stage,
            diagnostic,
            "returned empty output instead of a success artefact or `@@FAIL`.",
        )
        return False

    if raw.lstrip("\ufeff\r\n\t ").startswith(FAIL_SENTINEL):
        _write_protocol_failure(
            stage,
            diagnostic,
            "returned a failure sentinel with leading content; `@@FAIL` must be the first line.",
        )
        return False

    protocol_error = _success_protocol_error(raw, output_type)
    if protocol_error is not None:
        _write_protocol_failure(stage, diagnostic, protocol_error)
        return False

    _unlink(diagnostic)
    _atomic_write(output, raw)
    return True


def record_execution_failure(
    *,
    stage: str,
    output: Path,
    diagnostic: Path,
    exit_status: int,
) -> None:
    """Replace stale state with an external diagnostic for a failed runner pipeline."""
    _unlink(output)
    _write_protocol_failure(
        stage,
        diagnostic,
        (
            f"stage execution exited with status {exit_status} before a complete result "
            "was available; captured partial output was discarded."
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--output-type", required=True, choices=OUTPUT_TYPES)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--diagnostic", required=True, type=Path)
    parser.add_argument("--backend-exit-status", type=int)
    args = parser.parse_args()

    if args.backend_exit_status is not None:
        record_execution_failure(
            stage=args.stage,
            output=args.output,
            diagnostic=args.diagnostic,
            exit_status=args.backend_exit_status,
        )
        print(
            f"{args.stage}: stage execution failed; diagnostics: {args.diagnostic}",
            file=sys.stderr,
        )
        return 2

    raw = sys.stdin.read()
    success = enforce_result(
        raw,
        stage=args.stage,
        output_type=args.output_type,
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
