#!/usr/bin/env python3
"""Compile and validate a release-candidate LaTeX document."""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

FAIL_SENTINEL = "@@FAIL"
UNRESOLVED_MARKERS = (
    "There were undefined references",
    "There were undefined citations",
    "Citation `",
    "Reference `",
)
DIAGNOSTIC_SUFFIXES = (
    ".aux",
    ".bbl",
    ".bcf",
    ".blg",
    ".fdb_latexmk",
    ".fls",
    ".log",
    ".run.xml",
)
ERROR_MARKERS = (
    "undefined control sequence",
    "latex error:",
    "package biblatex error:",
    "pdftex error",
    "emergency stop",
    "fatal error",
    "runaway argument",
    "file ended while scanning",
    "error -",
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


def _failure_excerpt(log: str, stdout: str) -> str:
    for label, text in (("LaTeX log", log), ("latexmk output", stdout)):
        lines = text.splitlines()
        for index, line in enumerate(lines):
            lowered = line.lower()
            if line.lstrip().startswith("!") or any(
                marker in lowered for marker in ERROR_MARKERS
            ):
                start = max(0, index - 3)
                end = min(len(lines), index + 12)
                return f"{label} around first error:\n" + "\n".join(lines[start:end])
    return "latexmk output tail:\n" + "\n".join(stdout.splitlines()[-50:])


def _retain_failure_diagnostics(
    tmpdir: Path,
    stem: str,
    diagnostic_dir: Optional[Path],
    stdout: str,
) -> Optional[str]:
    if diagnostic_dir is None:
        return None
    try:
        diagnostic_dir.mkdir(parents=True, exist_ok=True)
        (diagnostic_dir / "latexmk.stdout.txt").write_text(stdout, encoding="utf-8")
        for suffix in DIAGNOSTIC_SUFFIXES:
            for source in (
                tmpdir / f"{stem}{suffix}",
                tmpdir / f"{stem}{suffix}-SAVE-ERROR",
            ):
                if source.is_file():
                    shutil.copy2(source, diagnostic_dir / source.name)
    except OSError as exc:
        return f"could not retain LaTeX diagnostics in {diagnostic_dir}: {exc}"
    return None


def compile_latex(
    input_path: Path,
    output_path: Path,
    *,
    latexmk: str = "latexmk",
    diagnostic_dir: Optional[Path] = None,
) -> None:
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
    source_dir = input_path.parent.resolve()
    # Keep the auxiliary directory below the source directory. TeX helper tools
    # are not uniformly portable when asked to write to an unrelated absolute
    # output directory, and the release source/bibliography already live here.
    with tempfile.TemporaryDirectory(
        prefix=".compiled-prose-latex-", dir=source_dir
    ) as tmp:
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
            cwd=source_dir,
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
            retention_error = _retain_failure_diagnostics(
                tmpdir,
                input_path.stem,
                diagnostic_dir,
                completed.stdout,
            )
            message = (
                f"latexmk failed with status {completed.returncode}:\n"
                f"{_failure_excerpt(log, completed.stdout)}"
            )
            if retention_error:
                message += f"\n{retention_error}"
            elif diagnostic_dir is not None:
                message += f"\nRetained diagnostics: {diagnostic_dir}"
            raise RuntimeError(message)
        unresolved = _unresolved_from_log(log)
        if unresolved:
            retention_error = _retain_failure_diagnostics(
                tmpdir,
                input_path.stem,
                diagnostic_dir,
                completed.stdout,
            )
            message = "unresolved LaTeX references/citations:\n" + "\n".join(unresolved)
            if retention_error:
                message += f"\n{retention_error}"
            elif diagnostic_dir is not None:
                message += f"\nRetained diagnostics: {diagnostic_dir}"
            raise RuntimeError(message)
        produced = tmpdir / f"{input_path.stem}.pdf"
        if not produced.is_file() or produced.stat().st_size == 0:
            retention_error = _retain_failure_diagnostics(
                tmpdir,
                input_path.stem,
                diagnostic_dir,
                completed.stdout,
            )
            message = "latexmk succeeded but did not produce a non-empty PDF"
            if retention_error:
                message += f"; {retention_error}"
            elif diagnostic_dir is not None:
                message += f"; retained diagnostics: {diagnostic_dir}"
            raise RuntimeError(message)
        shutil.copy2(produced, output_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--diagnostic-dir", type=Path)
    args = parser.parse_args()
    diagnostic_dir = args.diagnostic_dir or args.input.parent / "errors" / "latex"
    try:
        compile_latex(
            args.input,
            args.output,
            diagnostic_dir=diagnostic_dir,
        )
    except (OSError, RuntimeError) as exc:
        print(f"LaTeX validation failed: {exc}", file=sys.stderr)
        return 2
    print(f"LaTeX validation OK: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
