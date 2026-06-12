"""Branding schema + bundled-asset resolution.

Covers validation-contract assertions 1-8 (the schema enumerates every branding category),
9-11 (no absolute paths; assets resolved relative to the config file, no ``..`` escape), and
12-13 (load_branding surfaces agency identity and every proof section from config).
"""
import json
import os

import pytest

from customdecks.branding import (
    BRANDING_SCHEMA,
    PROOF_SECTIONS,
    BrandingError,
    load_branding,
    resolve_asset,
    resolve_assets_dir,
)
from customdecks.template_renderer import TemplateRenderer

_SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEMPLATE_CONFIG = os.path.join(_SKILL_DIR, "config.template.json")


def test_resolve_asset_is_relative_to_the_config_file_directory(tmp_path):
    config_path = str(tmp_path / "config.json")
    resolved = resolve_asset(config_path, "assets/logo.svg")
    assert resolved == os.path.join(str(tmp_path), "assets", "logo.svg")


def test_resolve_asset_rejects_absolute_paths(tmp_path):
    config_path = str(tmp_path / "config.json")
    with pytest.raises(BrandingError):
        resolve_asset(config_path, "/root/Sonny/logo.png")


def test_resolve_asset_rejects_parent_directory_escape(tmp_path):
    config_path = str(tmp_path / "config.json")
    with pytest.raises(BrandingError):
        resolve_asset(config_path, "../../etc/passwd")


def test_resolve_assets_dir_defaults_relative_to_config(tmp_path):
    config_path = str(tmp_path / "config.json")
    assert resolve_assets_dir({}, config_path) == os.path.join(str(tmp_path), "assets")
    assert resolve_assets_dir({"assets_dir": "brand"}, config_path) == os.path.join(str(tmp_path), "brand")


def test_schema_enumerates_all_eight_branding_categories():
    # agency identity: name, logo, sender, voice
    assert set(BRANDING_SCHEMA["agency"]) == {"name", "logo", "sender", "voice"}
    # proof: stat cards, case studies, client logos, founder-authority cards
    assert set(BRANDING_SCHEMA["proof"]) == {
        "stat_cards",
        "case_studies",
        "client_logos",
        "founder_authority",
    }


def test_load_branding_surfaces_identity_and_every_proof_section_from_config(tmp_path):
    config_path = str(tmp_path / "config.json")
    config = {
        "agency": {
            "name": "Northstar Outbound",
            "logo": "assets/logo.svg",
            "sender": {"name": "Casey Vault", "title": "Founder", "email": "casey@northstar.test"},
            "voice": "Direct and proof-led.",
        },
        "proof": {
            "stat_cards": [{"value": "3x", "label": "pipeline"}],
            "case_studies": [{"client": "Beta SaaS", "result": "18 meetings"}],
            "client_logos": ["assets/clients/beta.svg"],
            "founder_authority": [{"name": "Casey Vault", "credential": "10y outbound"}],
        },
    }
    branding = load_branding(config, config_path)

    assert branding["agency"]["name"] == "Northstar Outbound"
    assert branding["agency"]["logo"] == os.path.join(str(tmp_path), "assets", "logo.svg")
    assert branding["agency"]["sender"]["email"] == "casey@northstar.test"
    assert branding["agency"]["voice"] == "Direct and proof-led."

    assert branding["proof"]["stat_cards"] == [{"value": "3x", "label": "pipeline"}]
    assert branding["proof"]["case_studies"][0]["client"] == "Beta SaaS"
    assert branding["proof"]["client_logos"] == [os.path.join(str(tmp_path), "assets", "clients", "beta.svg")]
    assert branding["proof"]["founder_authority"][0]["credential"] == "10y outbound"


def test_template_config_populates_every_branding_category_with_examples():
    config = json.load(open(_TEMPLATE_CONFIG, encoding="utf-8"))
    agency = config["agency"]
    assert agency["name"] and agency["logo"] and agency["voice"]
    assert agency["sender"].get("name") and agency["sender"].get("email")
    for section in PROOF_SECTIONS:
        assert config["proof"][section], f"template config has no example for proof.{section}"


def test_template_config_assets_resolve_to_bundled_files_relative_to_config():
    config = json.load(open(_TEMPLATE_CONFIG, encoding="utf-8"))
    branding = load_branding(config, _TEMPLATE_CONFIG)
    # the bundled assets dir is found relative to the config file, and the example assets exist
    assert resolve_assets_dir(config, _TEMPLATE_CONFIG) == os.path.join(_SKILL_DIR, "assets")
    assert os.path.isfile(branding["agency"]["logo"])
    for logo in branding["proof"]["client_logos"]:
        assert os.path.isfile(logo)


def test_template_config_renders_a_branded_deck_with_all_proof_sections():
    config = json.load(open(_TEMPLATE_CONFIG, encoding="utf-8"))
    branding = load_branding(config, _TEMPLATE_CONFIG)
    tokens = {"headline": "H", "problem": "P", "solution": "S", "proof": "why",
              "cta_text": config["cta_text"], "cta_url": config["cta_url"]}
    prospect = {"name": "Jane Doe", "company": "Acme Corp", "website": "https://acme.test"}
    source = TemplateRenderer().build_marp_source(tokens, prospect, branding)
    assert config["agency"]["name"] in source
    assert "By the numbers" in source        # stat cards
    assert "Case studies" in source           # case studies
    assert "Trusted by" in source             # client logos
    assert "Who you are working with" in source  # founder authority


def test_load_branding_empty_config_yields_empty_identity_and_proof(tmp_path):
    branding = load_branding({}, str(tmp_path / "config.json"))
    assert branding["agency"] == {"name": "", "logo": None, "sender": {}, "voice": ""}
    assert branding["proof"] == {
        "stat_cards": [],
        "case_studies": [],
        "client_logos": [],
        "founder_authority": [],
    }
