#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from typing import Optional

OUTPUT_CONTRACTS = {
    "tex": "Return exactly one complete raw LaTeX document beginning with `\\documentclass` and ending with `\\end{document}`. Do not repeat or summarize the prompt.",
    "md": "Return only Markdown content. Do not repeat or summarize the prompt.",
}

FAILURE_CONTRACT = """If this stage cannot faithfully produce its declared success artefact under the prompt contract and authoritative source, fail instead of improvising:
- Put @@FAIL on the first line, with no leading whitespace or other content.
- Follow it with concise Markdown diagnostics localised to the authoritative source.
- State what authorial information is missing, ambiguous, contradictory, or unsupported; do not invent or apply a conceptual fix.
Do not mix a failure diagnostic into a successful artefact. Diagnostic stages should not use @@FAIL merely to report findings that are their normal declared output."""


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8").rstrip()


def render_prompt(
    *,
    system: str,
    target: str,
    stage: str,
    source_text: str,
    input_text: str,
    output_type: str,
    review: Optional[str] = None,
) -> str:
    try:
        output_instruction = OUTPUT_CONTRACTS[output_type]
    except KeyError as exc:
        raise ValueError(f"unsupported output type: {output_type}") from exc

    stage_input = input_text.rstrip()
    source = source_text.rstrip()

    # Keep rendered instruction layers in the documented order. The current
    # stage input is derived working material, not a conceptual-authority layer.
    sections = [
        system.rstrip(),
        "\n\n# Stage\n\n",
        stage.rstrip(),
        "\n\n# Target\n\n",
        target.rstrip(),
        "\n\n# Authoritative Source\n\n",
        source,
    ]

    # Draft/summarize commonly operate directly on the source. Avoid duplicating
    # a potentially large source payload when the working input is identical.
    if stage_input != source:
        sections.extend(
            [
                "\n\n# Stage Input (Derived Working Artefact; Non-Authoritative)\n\n",
                stage_input,
            ]
        )

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
            f"OUTPUT_TYPE: {output_type}\nSUCCESS: {output_instruction}\n\nFAILURE:\n{FAILURE_CONTRACT}",
        ]
    )
    return "".join(sections)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", required=True)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--source", required=True)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--review", required=False)
    ap.add_argument("--output-type", required=True, choices=OUTPUT_CONTRACTS)
    args = ap.parse_args()

    rendered = render_prompt(
        system=read(args.system),
        target=read(args.target),
        stage=read(args.stage),
        source_text=read(args.source),
        input_text=read(args.inp),
        output_type=args.output_type,
        review=read(args.review) if args.review else None,
    )
    sys.stdout.write(rendered)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
