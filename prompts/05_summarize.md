Summarize the authoritative source into a short, concise paragraph.
The summary should not just repeat or reword the source; it should compress it into a short paragraph without changing its meaning.

You must return a complete LaTeX document using this exact structure:

\documentclass{article}
\begin{document}
<concise summary, plain paragraphs only>
\end{document}

Rules:
- Return exactly one LaTeX document.
- Do not include any extra text before \documentclass or after \end{document}.
- Do not use headings, lists, or bullet points.
- Use only information present in the authoritative source.
- Do not add examples or invent citations.
- Preserve citations supplied by the authoritative source when the selected target requires citation support and the cited claim is retained in the summary.
- If the selected target requires citation support for a retained claim and the authoritative source does not supply it, use the failure branch of the output contract rather than inventing a reference.
- Do not repeat multiple illustrative examples; compress them into a single generalized statement.
- Keep the summary under 120 words.
- Output raw LaTeX only. No markdown or code fences.
