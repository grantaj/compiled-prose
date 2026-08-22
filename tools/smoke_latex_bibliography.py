#!/usr/bin/env python3
"""Provider-free smoke test for the release LaTeX/biblatex/biber toolchain."""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.validate_latex import compile_latex

SMOKE_DOCUMENT = r"""\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{microtype}
\usepackage{parskip}
\usepackage{hyperref}
\usepackage[english]{babel}
\usepackage[
  backend=biber,
  natbib=true
]{biblatex}
\addbibresource{references.bib}

\begin{document}
Provider-free release bibliography smoke test.
\nocite{*}
\printbibliography
\end{document}
"""


def smoke_bibliography(
    bibliography: Path, diagnostic_dir: Optional[Path] = None
) -> None:
    if not bibliography.is_file() or bibliography.stat().st_size == 0:
        raise RuntimeError(f"bibliography does not exist or is empty: {bibliography}")

    with tempfile.TemporaryDirectory(prefix="compiled-prose-bib-smoke-") as tmp:
        root = Path(tmp)
        source = root / "smoke.tex"
        copied_bibliography = root / "references.bib"
        output = root / "smoke.pdf"
        shutil.copy2(bibliography, copied_bibliography)
        source.write_text(SMOKE_DOCUMENT, encoding="utf-8")
        compile_latex(source, output, diagnostic_dir=diagnostic_dir)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bibliography", type=Path, required=True)
    parser.add_argument("--diagnostic-dir", type=Path)
    args = parser.parse_args()
    try:
        smoke_bibliography(args.bibliography, args.diagnostic_dir)
    except (OSError, RuntimeError) as exc:
        print(f"LaTeX bibliography smoke test failed: {exc}", file=sys.stderr)
        return 2
    print("LaTeX bibliography smoke test OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
