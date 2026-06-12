"""TemplateRenderer - turn processed copy tokens plus branding config into a Marp deck source,
then render it to a PDF and a PPTX.

Nothing about the agency is baked into this file. Agency identity (name, logo, sender, copy
voice) and proof (stat cards, case studies, client logos, founder-authority cards) all arrive
in the ``branding`` argument, sourced from config by ``branding.load_branding``. A proof
section whose config is empty is dropped from the deck, so a student with no case studies yet
ships a clean shorter deck instead of empty placeholder slides.

The PPTX is the artifact that gets uploaded and converted to Google Slides; the PDF is the
shareable export. The Marp source (.md) and any intermediate HTML are never the delivered
artifact. The renderer is injected as ``marp_runner(md_path, out_path, fmt)`` so tests do not
need ``npx``; ``npx_marp_runner`` builds the real one.
"""
import os
import shutil
import subprocess

FRONTMATTER = """---
marp: true
paginate: true
---

"""

SLIDE_BREAK = "\n\n---\n\n"


class RenderResult:
    def __init__(self, marp_path, pptx_path, pdf_path):
        self.marp_path = marp_path
        self.pptx_path = pptx_path
        self.pdf_path = pdf_path


class TemplateRenderer:
    def __init__(self, marp_runner=None):
        self._marp_runner = marp_runner or npx_marp_runner()

    def build_marp_source(self, tokens, prospect, branding=None):
        branding = branding or {}
        agency = branding.get("agency", {}) or {}
        proof = branding.get("proof", {}) or {}

        slides = [self._title_slide(prospect, agency)]
        if tokens.get("headline"):
            slides.append("## " + tokens["headline"])
        if tokens.get("problem"):
            slides.append("## The problem\n\n" + tokens["problem"])
        if tokens.get("solution"):
            slides.append("## What we do\n\n" + tokens["solution"])
        if tokens.get("proof"):
            slides.append("## Why it works\n\n" + tokens["proof"])
        slides.extend(self._proof_slides(proof))
        slides.append(self._cta_slide(tokens, prospect, agency))

        body = SLIDE_BREAK.join(s for s in slides if s)
        return FRONTMATTER + body + "\n"

    def render(self, tokens, prospect, out_dir, basename="deck", branding=None):
        os.makedirs(out_dir, exist_ok=True)
        marp_path = os.path.join(out_dir, basename + ".md")
        pptx_path = os.path.join(out_dir, basename + ".pptx")
        pdf_path = os.path.join(out_dir, basename + ".pdf")
        with open(marp_path, "w", encoding="utf-8") as fh:
            fh.write(self.build_marp_source(tokens, prospect, branding))
        self._marp_runner(marp_path, pdf_path, "pdf")
        self._marp_runner(marp_path, pptx_path, "pptx")
        return RenderResult(marp_path, pptx_path, pdf_path)

    # --- slide builders (every agency value comes from `agency` / `proof`, never hardcoded) --

    def _title_slide(self, prospect, agency):
        name = prospect.get("name", "")
        # Fall back to the prospect name, then a neutral title, so the deck never opens with a
        # bare "# " heading when the company field is empty.
        company = prospect.get("company", "") or name or "Tailored proposal"
        agency_name = agency.get("name", "")
        lines = ["# " + company]
        if agency_name:
            lines.append("\n### Prepared by " + agency_name + " for " + name)
        else:
            lines.append("\n### Prepared for " + name)
        if agency.get("logo"):
            lines.append("\n![h:80px](" + agency["logo"] + ")")
        if agency.get("voice"):
            lines.append("\n> " + agency["voice"])
        return "\n".join(lines)

    def _proof_slides(self, proof):
        slides = []

        stat_cards = proof.get("stat_cards") or []
        if stat_cards:
            rows = [f"- **{c.get('value', '')}** {c.get('label', '')}".rstrip() for c in stat_cards]
            slides.append("## By the numbers\n\n" + "\n".join(rows))

        case_studies = proof.get("case_studies") or []
        if case_studies:
            blocks = []
            for c in case_studies:
                client = c.get("client", "")
                result = c.get("result", "")
                # Only join with " - " when there is a result, so a result that itself ends
                # in a dash (e.g. "conversion-driven") is never truncated by a blanket rstrip.
                head = f"**{client}** - {result}" if result else f"**{client}**"
                detail = c.get("detail", "")
                blocks.append(head + ("\n" + detail if detail else ""))
            slides.append("## Case studies\n\n" + "\n\n".join(blocks))

        client_logos = proof.get("client_logos") or []
        if client_logos:
            imgs = [f"![h:60px]({path})" for path in client_logos]
            slides.append("## Trusted by\n\n" + " ".join(imgs))

        founders = proof.get("founder_authority") or []
        if founders:
            rows = []
            for f in founders:
                name = f.get("name", "")
                cred = f.get("credential", "")
                rows.append(f"- **{name}** - {cred}" if cred else f"- **{name}**")
            slides.append("## Who you are working with\n\n" + "\n".join(rows))

        return slides

    def _cta_slide(self, tokens, prospect, agency):
        cta_text = tokens.get("cta_text", "")
        cta_url = tokens.get("cta_url", "")
        lines = ["## " + cta_text, "\n[" + cta_text + "](" + cta_url + ")"]

        sender = agency.get("sender", {}) or {}
        signoff = ", ".join(part for part in (sender.get("name", ""), sender.get("title", "")) if part)
        if signoff:
            lines.append("\n" + signoff)
        if sender.get("email"):
            lines.append(sender["email"])

        website = prospect.get("website", "")
        if website:
            lines.append("\n" + website)
        return "\n".join(lines)


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
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "").strip()
            raise RuntimeError(f"marp render failed ({fmt}): {detail}") from exc

    return run
