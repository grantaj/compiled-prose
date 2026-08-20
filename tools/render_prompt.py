#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from typing import Optional

OUTPUT_CONTRACTS = {
    "tex": "Return only raw LaTeX content. Do not repeat or summarize the prompt.",
    "md": "Return only Markdown content. Do not repeat or summarize the prompt.",
}


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8").rstrip()


def render_prompt(
    *,
    system: str,
    target: str,
    stage: str,
    input_text: str,
    output_type: str,
    review: Optional[str] = None,
) -> str:
    try:
        output_instruction = OUTPUT_CONTRACTS[output_type]
    except KeyError as exc:
        raise ValueError(f"unsupported output type: {output_type}") from exc

    sections = [
        system.rstrip(),
        "\n\n# Target\n\n",
        target.rstrip(),
        "\n\n# Stage\n\n",
        stage.rstrip(),
        "\n\n# Input (Markdown)\n\n",
        input_text.rstrip(),
    ]

    if review is not None:
        sections.extend(
            [
                "\n\n# Peer Review (Markdown, Diagnostic Only)\n\n",
                review.rstrip(),
            ]
        )

    sections.extend(
        [
            "\n\n# Output Contract\n\n",
            f"OUTPUT_TYPE: {output_type}\n{output_instruction}",
        ]
    )
    return "".join(sections)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", required=True)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--review", required=False)
    ap.add_argument("--output-type", required=True, choices=OUTPUT_CONTRACTS)
    args = ap.parse_args()

    rendered = render_prompt(
        system=read(args.system),
        target=read(args.target),
        stage=read(args.stage),
        input_text=read(args.inp),
        output_type=args.output_type,
        review=read(args.review) if args.review else None,
    )
    sys.stdout.write(rendered)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
