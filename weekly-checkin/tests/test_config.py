"""config validation: required keys, non-empty clients, and cross-client uniqueness."""
import pytest

from weeklycheckin.config import ConfigError, validate_config


def _cfg(**over):
    base = {
        "smartlead_api_key": "k",
        "google_sheet_id": "s",
        "google_oauth": {"credentials_file": "c", "token_file": "t"},
        "clients": [
            {"name": "Acme", "rep_tabs": ["Alice"], "smartlead_campaign_ids": [1]},
        ],
    }
    base.update(over)
    return base


def test_missing_smartlead_api_key_raises():
    cfg = _cfg()
    del cfg["smartlead_api_key"]
    with pytest.raises(ConfigError) as exc:
        validate_config(cfg)
    assert "smartlead_api_key" in str(exc.value)


def test_missing_clients_raises():
    cfg = _cfg()
    del cfg["clients"]
    with pytest.raises(ConfigError) as exc:
        validate_config(cfg)
    assert "clients" in str(exc.value)


def test_empty_clients_raises():
    with pytest.raises(ConfigError) as exc:
        validate_config(_cfg(clients=[]))
    assert "clients" in str(exc.value)


def test_duplicate_rep_tab_across_clients_raises_with_tab_name():
    cfg = _cfg(
        clients=[
            {"name": "Acme", "rep_tabs": ["Alice", "Bob"], "smartlead_campaign_ids": [1]},
            {"name": "Beta", "rep_tabs": ["Bob"], "smartlead_campaign_ids": [2]},
        ]
    )
    with pytest.raises(ConfigError) as exc:
        validate_config(cfg)
    assert "Bob" in str(exc.value)


def test_duplicate_campaign_id_across_clients_raises_with_id():
    cfg = _cfg(
        clients=[
            {"name": "Acme", "rep_tabs": ["Alice"], "smartlead_campaign_ids": [7]},
            {"name": "Beta", "rep_tabs": ["Carol"], "smartlead_campaign_ids": [7]},
        ]
    )
    with pytest.raises(ConfigError) as exc:
        validate_config(cfg)
    assert "7" in str(exc.value)


def test_valid_config_passes():
    assert validate_config(_cfg()) is not None
