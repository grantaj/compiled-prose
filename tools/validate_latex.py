#!/usr/bin/env python3
"""Compile and validate a release-candidate LaTeX document."""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FAIL_SENTINEL = "@@FAIL"
UNRESOLVED_MARKERS = (
    "There were undefined references",
    "There were undefined citations",
    "Citation `",
    "Reference `",
)


def validate_document_text(text: str) -> list[str]:
    errors: list[str] = []
    content = text.lstrip("\ufeff")
    if FAIL_SENTINEL in content:
        errors.append("compiler failure sentinel @@FAIL is present")
    if not content.startswith("\\documentclass"):
        errors.append("document must start with \\documentclass")
    begin = content.find("\\begin{document}")
    end = content.rfind("\\end{document}")
    if begin < 0:
        errors.append("missing \\begin{document}")
    if end < 0:
        errors.append("missing \\end{document}")
    elif begin >= 0 and end < begin:
        errors.append("\\end{document} appears before \\begin{document}")
    elif content[end + len("\\end{document}") :].strip():
        errors.append("non-whitespace content follows \\end{document}")
    return errors


def _unresolved_from_log(log: str) -> list[str]:
    lines: list[str] = []
    for line in log.splitlines():
        if (
            any(marker in line for marker in UNRESOLVED_MARKERS)
            and "undefined" in line.lower()
        ):
            lines.append(line.strip())
    return lines


def compile_latex(input_path: Path, output_path: Path, *, latexmk: str = "latexmk") -> None:
    executable = shutil.which(latexmk)
    if executable is None:
        raise RuntimeError(
            "latexmk is required for release validation; install latexmk and a LaTeX distribution"
        )

    text = input_path.read_text(encoding="utf-8")
    static_errors = validate_document_text(text)
    if static_errors:
        raise RuntimeError("; ".join(static_errors))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="compiled-prose-latex-") as tmp:
        tmpdir = Path(tmp)
        command = [
            executable,
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            f"-outdir={tmpdir}",
            input_path.name,
        ]
        completed = subprocess.run(
            command,
            cwd=input_path.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        log_path = tmpdir / f"{input_path.stem}.log"
        log = (
            log_path.read_text(encoding="utf-8", errors="replace")
            if log_path.is_file()
            else completed.stdout
        )
        if completed.returncode != 0:
            tail = "\n".join(completed.stdout.splitlines()[-25:])
            raise RuntimeError(
                f"latexmk failed with status {completed.returncode}:\n{tail}"
            )
        unresolved = _unresolved_from_log(log)
        if unresolved:
            raise RuntimeError(
                "unresolved LaTeX references/citations:\n" + "\n".join(unresolved)
            )
        produced = tmpdir / f"{input_path.stem}.pdf"
        if not produced.is_file() or produced.stat().st_size == 0:
            raise RuntimeError("latexmk succeeded but did not produce a non-empty PDF")
        shutil.copy2(produced, output_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        compile_latex(args.input, args.output)
    except (OSError, RuntimeError) as exc:
        print(f"LaTeX validation failed: {exc}", file=sys.stderr)
        return 2
    print(f"LaTeX validation OK: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
