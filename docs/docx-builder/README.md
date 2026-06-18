# Styled .docx builder (reusable)

A deterministic Word-doc builder any skill can copy in to deliver a styled `.docx`.

## Why it exists

The Cowork Google Drive connector uploads plain text only: no fonts, color, weight,
alignment, or table shading. To ship a styled doc, the model writes structured JSON
(content only) and `build_docx.py` renders the look. The styling lives in code, not in
the model's per-run judgment, so every doc comes out identical instead of drifting run
to run.

This pattern is already proven in two skills:
- `pre-brief/assets/build_brief_docx.py`
- `client-proposal-doc-builder/assets/build_proposal_docx.py`

`build_docx.py` here is the generalized version - the superset of both, with the
RevCentric-specific bits pulled out into CONFIG and a generic block schema.

## How to reuse it (copy-in, not import)

Skills ship as standalone ZIPs (`.github/workflows/build-skill-zips.yml` zips each
top-level skill dir on its own), so a shared import will not travel with the skill.
Copy the file in:

1. Copy `build_docx.py` into your new skill's `assets/`.
2. Edit the `CONFIG` block for your palette / font / sizes (hex without `#`).
3. Keep the generic blocks; add or delete specialized ones. The render loop in
   `build()` is the single place to wire a new block `type`.
4. Document your final block schema in the script's docstring so the model knows
   exactly what JSON to emit.

Run pattern (same for every skill):

```
python3 build_docx.py content.json "Output Name.docx"
```

Needs `python-docx` (`pip install python-docx` if the runtime lacks it).

## What you get for free

- Arial document-wide (set on the `Normal` style with `w:rFonts` fallbacks).
- 3-color palette: navy headings, near-black title, gray labels/quotes.
- Named type scale (title 26 / h1 16 / h2 12.5 / body 10.5 / label 9) for clear hierarchy.
- Explicit paragraph spacing + `keep_with_next` on headings so a heading never strands
  at a page bottom.
- 0.9in margins.
- Tables: shaded header rows, emphasis rows, green/red status cells, thin gray borders.
- `**bold**` spans honored in every text field.
- Two guards that fail loudly: em-dashes anywhere in the content, and any unknown block
  type. Better a clear error than a silently wrong doc.

## Block schema

`title_block` is an optional top-level key. `blocks` is an ordered list - reorder it to
reorder the doc, no code change. Full schema with examples lives in the `build_docx.py`
docstring. Block types: `h1`, `h2`, `h3`, `p`, `bullets`, `numbered`, `table`,
`status_table`, `signature`, `spacer`.

## Drop-in paragraph for a new skill's SKILL.md

Paste this into the skill, adjusting the JSON keys to match the schema you settled on:

> **Delivering the .docx.** Do not style the document yourself and do not rely on the
> Drive connector for formatting - it uploads plain text only. Instead, write the
> document content as JSON matching the schema in `assets/build_docx.py`, then run
> `python3 assets/build_docx.py content.json "<Output Name>.docx"` and deliver the
> resulting file. All styling (fonts, colors, headings, tables, spacing) is handled by
> the builder so every document looks identical. Use `**bold**` for emphasis inside any
> text field. Never use em-dashes; the builder rejects them and will tell you which
> field to rewrite.
