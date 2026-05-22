"""Email verification waterfall.

Provider order (cheapest first):
1. MillionVerifier
2. ZeroBounce
3. Prospeo
4. LeadMagic

Stops at first definitive result (valid / invalid / catch_all).
Returns "unknown" only if all providers fail or return unknown.
"""
from __future__ import annotations

import os
import time

import requests


class MillionVerifierClient:
    BASE = "https://api.millionverifier.com/api/v3"

    def __init__(self):
        self.api_key = os.getenv("MILLIONVERIFIER_API_KEY")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def verify(self, email: str) -> dict:
        resp = requests.get(
            f"{self.BASE}/",
            params={"api": self.api_key, "email": email},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        result_map = {
            "ok": "valid",
            "catch_all": "catch_all",
            "unknown": "unknown",
            "error": "invalid",
            "disposable": "invalid",
            "invalid": "invalid",
        }
        return {
            "status": result_map.get(data.get("result", "unknown"), "unknown"),
            "provider": "millionverifier",
        }


class ZeroBounceClient:
    BASE = "https://api.zerobounce.net/v2"

    def __init__(self):
        self.api_key = os.getenv("ZEROBOUNCE_API_KEY")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def verify(self, email: str) -> dict:
        resp = requests.get(
            f"{self.BASE}/validate",
            params={"api_key": self.api_key, "email": email},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        result_map = {
            "valid": "valid",
            "invalid": "invalid",
            "catch-all": "catch_all",
            "unknown": "unknown",
            "spamtrap": "invalid",
            "abuse": "invalid",
            "do_not_mail": "invalid",
        }
        return {
            "status": result_map.get(data.get("status", "unknown"), "unknown"),
            "provider": "zerobounce",
        }


class ProspeoClient:
    BASE = "https://api.prospeo.io"

    def __init__(self):
        self.api_key = os.getenv("PROSPEO_API_KEY")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def verify(self, email: str) -> dict:
        resp = requests.post(
            f"{self.BASE}/email-verifier",
            json={"email": email},
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json().get("response", {})
        if data.get("isValidFormat") and data.get("isDeliverable"):
            status = "valid"
        elif data.get("isCatchAll"):
            status = "catch_all"
        elif data.get("isDeliverable") is False:
            status = "invalid"
        else:
            status = "unknown"
        return {"status": status, "provider": "prospeo"}


class LeadMagicClient:
    BASE = "https://api.leadmagic.io/email"

    def __init__(self):
        self.api_key = os.getenv("LEADMAGIC_API_KEY")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def verify(self, email: str) -> dict:
        resp = requests.post(
            f"{self.BASE}/validate",
            json={"email": email},
            headers={"X-API-Key": self.api_key, "Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        result_map = {
            "valid": "valid",
            "invalid": "invalid",
            "catch_all": "catch_all",
            "unknown": "unknown",
        }
        return {
            "status": result_map.get(data.get("status", "unknown"), "unknown"),
            "provider": "leadmagic",
        }


class EmailVerifier:
    """Waterfall verifier — tries providers cheapest-first, stops at first definitive answer."""

    def __init__(self):
        candidates = [MillionVerifierClient(), ZeroBounceClient(), ProspeoClient(), LeadMagicClient()]
        self.providers = [p for p in candidates if p.available]

        if not self.providers:
            raise ValueError(
                "No email validation keys configured. Add at least one of: "
                "MILLIONVERIFIER_API_KEY, ZEROBOUNCE_API_KEY, PROSPEO_API_KEY, LEADMAGIC_API_KEY"
            )

    @property
    def provider_names(self) -> str:
        return " → ".join(p.__class__.__name__.replace("Client", "") for p in self.providers)

    def verify_email(self, email: str) -> dict:
        for provider in self.providers:
            try:
                result = provider.verify(email)
                if result["status"] in ("valid", "invalid", "catch_all"):
                    return result
                time.sleep(0.1)
            except Exception:
                time.sleep(0.1)
                continue

        return {"status": "unknown", "provider": "none"}
