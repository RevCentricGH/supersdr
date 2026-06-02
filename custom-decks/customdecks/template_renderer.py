"""TemplateRenderer - turn processed copy tokens into a Marp deck source, then render it to
a PDF and a PPTX.

The PPTX is the artifact that gets uploaded and converted to Google Slides; the PDF is the
shareable export. The Marp source (.md) and any intermediate HTML are never the delivered
artifact - they exist only to be rendered. The renderer is injected as
``marp_runner(md_path, out_path, fmt)`` so tests do not need ``npx``; ``npx_marp_runner``
builds the real one.
"""
import os
import shutil
import subprocess

DECK_TEMPLATE = """---
marp: true
paginate: true
---

# {company}

### Prepared for {name}

---

## {headline}

---

## The problem

{problem}

---

## What we do

{solution}

---

## Proof

{proof}

---

## {cta_text}

[{cta_text}]({cta_url})

{website}
"""


class RenderResult:
    def __init__(self, marp_path, pptx_path, pdf_path):
        self.marp_path = marp_path
        self.pptx_path = pptx_path
        self.pdf_path = pdf_path


class TemplateRenderer:
    def __init__(self, marp_runner=None):
        self._marp_runner = marp_runner or npx_marp_runner()

    def build_marp_source(self, tokens, prospect):
        return DECK_TEMPLATE.format(
            company=prospect.get("company", ""),
            name=prospect.get("name", ""),
            website=prospect.get("website", ""),
            headline=tokens.get("headline", ""),
            problem=tokens.get("problem", ""),
            solution=tokens.get("solution", ""),
            proof=tokens.get("proof", ""),
            cta_text=tokens.get("cta_text", ""),
            cta_url=tokens.get("cta_url", ""),
        )

    def render(self, tokens, prospect, out_dir, basename="deck"):
        os.makedirs(out_dir, exist_ok=True)
        marp_path = os.path.join(out_dir, basename + ".md")
        pptx_path = os.path.join(out_dir, basename + ".pptx")
        pdf_path = os.path.join(out_dir, basename + ".pdf")
        with open(marp_path, "w", encoding="utf-8") as fh:
            fh.write(self.build_marp_source(tokens, prospect))
        self._marp_runner(marp_path, pdf_path, "pdf")
        self._marp_runner(marp_path, pptx_path, "pptx")
        return RenderResult(marp_path, pptx_path, pdf_path)


def npx_marp_runner(npx="npx"):
    """Real Marp renderer via marp-cli. Uses --pptx-editable when LibreOffice (soffice) is
    available so the Slides keep selectable text and live hyperlinks; otherwise falls back to
    image-based --pptx."""

    def run(md_path, out_path, fmt):
        flag = "--pdf"
        if fmt == "pptx":
            flag = "--pptx-editable" if shutil.which("soffice") else "--pptx"
        cmd = [npx, "-y", "@marp-team/marp-cli@latest", md_path, flag,
               "--allow-local-files", "-o", out_path]
        subprocess.run(cmd, check=True, capture_output=True, text=True)

    return run
