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


def _citation_output_contract(bibliography_name: str) -> str:
    return f"""CITATION_FORMAT:
- Citation metadata is supplied separately from the authoritative source. It provides only verified bibliographic rendering metadata and stable citation keys; it does not add claims, evidence, or conceptual authority.
- Use only BibTeX keys present in that supplied metadata. Never invent, rename, or infer a citation key.
- Preserve source-supplied citations and keep them attached to the claims they support.
- In LaTeX output, use `\\parencite{{key}}` for ordinary parenthetical citations and `\\textcite{{key}}` only where the citation is grammatically part of the sentence.
- Configure biblatex with `\\usepackage[backend=biber,style=authoryear]{{biblatex}}` and `\\addbibresource{{{bibliography_name}}}`.
- Include `\\printbibliography` exactly once near the end of the document.
- Do not emit a `thebibliography` environment or hand-write bibliography entries; the supplied bibliography file is the rendering source."""


def render_prompt(
    *,
    system: str,
    target: str,
    stage: str,
    source_text: str,
    input_text: str,
    output_type: str,
    review: Optional[str] = None,
    bibliography_text: Optional[str] = None,
    bibliography_name: Optional[str] = None,
) -> str:
    try:
        output_instruction = OUTPUT_CONTRACTS[output_type]
    except KeyError as exc:
        raise ValueError(f"unsupported output type: {output_type}") from exc

    if (bibliography_text is None) != (bibliography_name is None):
        raise ValueError("bibliography_text and bibliography_name must be supplied together")

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

    if bibliography_text is not None and bibliography_name is not None:
        sections.extend(
            [
                "\n\n# Citation Metadata (Bibliographic Only; Non-Conceptual)\n\n",
                f"BIBLIOGRAPHY_RESOURCE: {bibliography_name}\n\n",
                bibliography_text.rstrip(),
            ]
        )

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

    output_contract = f"OUTPUT_TYPE: {output_type}\nSUCCESS: {output_instruction}"
    if output_type == "tex" and bibliography_name is not None:
        output_contract += "\n\n" + _citation_output_contract(bibliography_name)
    output_contract += f"\n\nFAILURE:\n{FAILURE_CONTRACT}"

    sections.extend(["\n\n# Output Contract\n\n", output_contract])
    return "".join(sections)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", required=True)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--source", required=True)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--review", required=False)
    ap.add_argument("--bibliography", required=False)
    ap.add_argument("--output-type", required=True, choices=OUTPUT_CONTRACTS)
    args = ap.parse_args()

    bibliography = Path(args.bibliography) if args.bibliography else None
    rendered = render_prompt(
        system=read(args.system),
        target=read(args.target),
        stage=read(args.stage),
        source_text=read(args.source),
        input_text=read(args.inp),
        output_type=args.output_type,
        review=read(args.review) if args.review else None,
        bibliography_text=read(str(bibliography)) if bibliography else None,
        bibliography_name=bibliography.name if bibliography else None,
    )
    sys.stdout.write(rendered)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
