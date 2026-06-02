"""TemplateRenderer: build Marp source from processed tokens and render it to PDF + PPTX.

Covers validation-contract assertions 18-19. The Marp runner is injected so the unit tests
stay fast and credential-free; the real `npx marp` render (and the %PDF- check) runs in the
end-to-end step recorded in DEV_STATUS.md.
"""
import os

from customdecks.template_renderer import TemplateRenderer

TOKENS = {
    "headline": "Acme ships faster",
    "problem": "Manual handoffs slow you down",
    "solution": "Automate the handoffs",
    "proof": "Teams cut cycle time 30%",
    "cta_text": "Book a call",
    "cta_url": "https://book.test/jane",
}
PROSPECT = {"name": "Jane Doe", "company": "Acme Corp", "website": "https://acme.test"}

BRANDING = {
    "agency": {
        "name": "Northstar Outbound",
        "logo": "/tmp/brand/logo.svg",
        "sender": {"name": "Casey Vault", "title": "Founder", "email": "casey@northstar.test"},
        "voice": "Direct and proof-led, never generic.",
    },
    "proof": {
        "stat_cards": [{"value": "3x", "label": "pipeline in 90 days"}],
        "case_studies": [{"client": "Beta SaaS", "result": "18 meetings in 30 days", "detail": "Rebuilt outbound."}],
        "client_logos": ["/tmp/brand/clients/beta.svg"],
        "founder_authority": [{"name": "Casey Vault", "credential": "10 years running B2B outbound"}],
    },
}


class FakeRunner:
    """Records every render request and writes a placeholder file so render() can return
    real paths without invoking npx."""

    def __init__(self):
        self.calls = []

    def __call__(self, md_path, out_path, fmt):
        self.calls.append((md_path, out_path, fmt))
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(fmt)


def test_marp_source_contains_company_and_clickable_cta():
    source = TemplateRenderer().build_marp_source(TOKENS, PROSPECT, BRANDING)
    assert "Acme Corp" in source
    assert "[Book a call](https://book.test/jane)" in source
    assert "marp: true" in source


def test_marp_source_renders_agency_identity_from_config():
    source = TemplateRenderer().build_marp_source(TOKENS, PROSPECT, BRANDING)
    # agency name, logo, sender identity, and copy voice all come from the branding config
    assert "Northstar Outbound" in source
    assert "/tmp/brand/logo.svg" in source
    assert "Casey Vault" in source
    assert "casey@northstar.test" in source
    assert "Direct and proof-led, never generic." in source


def test_marp_source_renders_every_proof_section_from_config():
    source = TemplateRenderer().build_marp_source(TOKENS, PROSPECT, BRANDING)
    # stat cards
    assert "3x" in source and "pipeline in 90 days" in source
    # case studies
    assert "Beta SaaS" in source and "18 meetings in 30 days" in source
    # client logos (rendered as image references to the resolved asset path)
    assert "/tmp/brand/clients/beta.svg" in source
    # founder-authority cards
    assert "10 years running B2B outbound" in source


def test_empty_proof_sections_are_omitted_from_the_deck():
    no_proof = {
        "agency": BRANDING["agency"],
        "proof": {"stat_cards": [], "case_studies": [], "client_logos": [], "founder_authority": []},
    }
    source = TemplateRenderer().build_marp_source(TOKENS, PROSPECT, no_proof)
    # agency identity still renders in this variant (name, logo, sender, voice all from config)...
    assert "Northstar Outbound" in source
    assert "/tmp/brand/logo.svg" in source
    assert "Casey Vault" in source
    assert "Direct and proof-led, never generic." in source
    # ...but no empty proof section headers are emitted
    assert "By the numbers" not in source
    assert "Case studies" not in source
    assert "Trusted by" not in source
    assert "Who you are working with" not in source


def test_no_branding_leaks_no_agency_identity_or_proof():
    # With no branding config, the template must supply none of the agency values itself -
    # proof that nothing brand-identifying is hardcoded in the template.
    source = TemplateRenderer().build_marp_source(TOKENS, PROSPECT, None)
    for leak in ("Northstar Outbound", "Casey Vault", "Beta SaaS", "RevCentric", "3x"):
        assert leak not in source


def test_render_writes_source_and_renders_pdf_and_pptx(tmp_path):
    runner = FakeRunner()
    result = TemplateRenderer(marp_runner=runner).render(TOKENS, PROSPECT, str(tmp_path))
    # the Marp source is written...
    assert result.marp_path.endswith(".md")
    assert os.path.exists(result.marp_path)
    # ...and the uploaded artifact is the rendered pptx, not the source or html
    assert result.pptx_path.endswith(".pptx")
    assert result.pdf_path.endswith(".pdf")
    formats = {fmt for (_, _, fmt) in runner.calls}
    assert formats == {"pdf", "pptx"}
    assert os.path.exists(result.pptx_path)
    assert os.path.exists(result.pdf_path)
