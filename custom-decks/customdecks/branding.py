"""Branding - the agency-identity and proof config schema, plus bundled-asset resolution.

Everything that makes a deck *the student's own agency* lives in config, never in the deck
template. ``BRANDING_SCHEMA`` enumerates the branding keys the deck reads: agency identity
(name, logo, sender, voice) and proof (stat cards, case studies, client logos, founder-
authority cards). ``load_branding`` turns a raw config dict into the structured object the
renderer consumes, resolving every asset path *relative to the config file's directory* so
there are no machine-specific absolute paths anywhere. An asset path that is absolute or that
escapes the config directory via ``..`` is rejected rather than silently followed.
"""
import os

# The config schema. Identity = how the deck is branded; proof = the agency's evidence.
IDENTITY_FIELDS = ("name", "logo", "sender", "voice")
PROOF_SECTIONS = ("stat_cards", "case_studies", "client_logos", "founder_authority")
ASSET_FIELDS = ("logo",)  # identity fields that name a bundled asset file
ASSET_PROOF_SECTIONS = ("client_logos",)  # proof sections that are lists of asset files

BRANDING_SCHEMA = {
    "agency": IDENTITY_FIELDS,
    "assets_dir": "assets",  # default subdir, resolved relative to the config file
    "proof": PROOF_SECTIONS,
}


class BrandingError(Exception):
    """A branding/asset path is unusable (absolute, or escapes the config directory)."""


def _config_dir(config_path):
    return os.path.dirname(os.path.abspath(config_path))


def resolve_asset(config_path, rel_path):
    """Resolve ``rel_path`` against the config file's directory.

    Rejects absolute paths and any path that normalizes to a location outside the config
    directory (``..`` traversal), so a config can only ever point at its own bundled assets.
    """
    if not rel_path:
        return None
    if not isinstance(rel_path, str):
        raise BrandingError(f"asset path must be a string, got {type(rel_path).__name__}: {rel_path!r}")
    if os.path.isabs(rel_path):
        raise BrandingError(f"asset path must be relative to the config file, not absolute: {rel_path}")
    base = _config_dir(config_path)
    resolved = os.path.normpath(os.path.join(base, rel_path))
    if resolved != base and not resolved.startswith(base + os.sep):
        raise BrandingError(f"asset path escapes the config directory: {rel_path}")
    return resolved


def resolve_assets_dir(config, config_path):
    """The bundled assets directory, resolved relative to the config file (default ``assets``)."""
    return resolve_asset(config_path, config.get("assets_dir", BRANDING_SCHEMA["assets_dir"]))


def load_branding(config, config_path):
    """Build the structured branding object the renderer reads, with assets resolved.

    Returns ``{"agency": {name, logo, sender, voice}, "proof": {<four sections>}}``. Missing
    keys come back empty so a deck with no proof simply omits those sections.
    """
    agency_cfg = config.get("agency", {}) or {}
    agency = {
        "name": agency_cfg.get("name", ""),
        "logo": resolve_asset(config_path, agency_cfg.get("logo")),
        "sender": agency_cfg.get("sender", {}) or {},
        "voice": agency_cfg.get("voice", ""),
    }

    proof_cfg = config.get("proof", {}) or {}
    proof = {section: list(proof_cfg.get(section, []) or []) for section in PROOF_SECTIONS}
    proof["client_logos"] = [
        r for r in (resolve_asset(config_path, p) for p in proof["client_logos"]) if r
    ]

    return {"agency": agency, "proof": proof}
