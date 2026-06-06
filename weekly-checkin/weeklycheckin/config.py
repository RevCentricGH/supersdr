"""Load and validate the weekly-checkin config.

``load_config`` reads config.json and validates it, failing fast with a clear message: the
four required keys must be present and non-empty, ``clients`` must be a non-empty array, and
no ``rep_tab`` or ``smartlead_campaign_id`` may appear under more than one client (a duplicate
would make a call or campaign ambiguous across clients).
"""
import json

REQUIRED_KEYS = ("smartlead_api_key", "google_sheet_id", "google_oauth", "clients")


class ConfigError(ValueError):
    pass


def load_config(path):
    with open(path, encoding="utf-8") as fh:
        config = json.load(fh)
    validate_config(config)
    return config


def validate_config(config):
    for key in REQUIRED_KEYS:
        if key not in config or config[key] in (None, ""):
            raise ConfigError(f"config is missing required key '{key}'")
    clients = config["clients"]
    if not isinstance(clients, list) or not clients:
        raise ConfigError("config 'clients' must be a non-empty array")
    seen_tabs = set()
    seen_campaigns = set()
    for client in clients:
        for tab in client.get("rep_tabs", []):
            if tab in seen_tabs:
                raise ConfigError(
                    f"duplicate rep_tab '{tab}' across clients; each rep tab must belong to exactly one client"
                )
            seen_tabs.add(tab)
        for cid in client.get("smartlead_campaign_ids", []):
            if cid in seen_campaigns:
                raise ConfigError(
                    f"duplicate smartlead_campaign_id '{cid}' across clients; each campaign must belong to exactly one client"
                )
            seen_campaigns.add(cid)
    return config
