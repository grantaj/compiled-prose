Summarize the input into a short, concise paragraph.
The summary should not just repeat or reword the input it should summarize it into a short paragraph.

You must return a complete LaTeX document using this exact structure:

\documentclass{article}
\begin{document}
<concise summary, plain paragraphs only>
\end{document}

Rules:
- Return exactly one LaTeX document.
- Do not include any extra text before \documentclass or after \end{document}.
- Do not use headings, lists, or bullet points.
- Use only information present in the input.
- Do not add examples or citations.
- Do not repeat multiple illustrative examples; compress them into a single generalized statement.
- Keep the summary under 120 words.
- Output raw LaTeX only. No markdown or code fences.
