"""Phone number validation via Twilio Lookup.

Checks line type (mobile / landline / voip) for each number.
For SDR cold calling, mobile is best, landline is workable, voip should be flagged.

Phone statuses:
  MOBILE     — confirmed mobile number (best for cold calling)
  LANDLINE   — confirmed landline (can still dial, lower connect rate)
  VOIP       — VoIP line (typically low connect rate, often skipped)
  INVALID    — number does not exist (Twilio 404)
  UNVERIFIED — number came from Apollo but Twilio keys not set, so line type is unknown.
               The number may be real and dialable — we just haven't confirmed whether
               it's mobile, landline, or VoIP. Treat it as a best-effort number.
  MISSING    — no phone number found for this contact at all

Requires TWILIO_ACCOUNT_SID + TWILIO_AUTH_TOKEN in .env.
Without these keys, all phones with numbers are marked UNVERIFIED.
"""
from __future__ import annotations

import os
import time
from base64 import b64encode

import requests

LOOKUP_URL = "https://lookups.twilio.com/v2/PhoneNumbers/{number}"

# Twilio line_type values → normalized status
_TYPE_MAP = {
    "mobile":        "MOBILE",
    "landline":      "LANDLINE",
    "voip":          "VOIP",
    "nonFixedVoip":  "VOIP",
    "tollFree":      "LANDLINE",
}


class PhoneValidator:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token  = os.getenv("TWILIO_AUTH_TOKEN",  "")

    @property
    def available(self) -> bool:
        return bool(self.account_sid and self.auth_token)

    def _auth_header(self) -> str:
        token = b64encode(f"{self.account_sid}:{self.auth_token}".encode()).decode()
        return f"Basic {token}"

    def lookup(self, phone: str) -> dict:
        """Return normalized phone info for one number.

        Returns: {status, line_type, carrier, formatted}
          status: MOBILE | LANDLINE | VOIP | INVALID | UNVERIFIED
        """
        if not phone or not phone.strip():
            return {"status": "MISSING", "line_type": "", "carrier": "", "formatted": ""}

        try:
            resp = requests.get(
                LOOKUP_URL.format(number=phone.strip()),
                params={"Fields": "line_type_intelligence"},
                headers={"Authorization": self._auth_header()},
                timeout=15,
            )
            if resp.status_code == 404:
                return {"status": "INVALID", "line_type": "", "carrier": "", "formatted": phone}
            if resp.status_code == 429:
                time.sleep(2)
                return self.lookup(phone)
            if resp.status_code != 200:
                return {"status": "UNVERIFIED", "line_type": "", "carrier": "", "formatted": phone}

            data = resp.json()
            lti  = data.get("line_type_intelligence") or {}
            raw_type = lti.get("type") or ""
            status   = _TYPE_MAP.get(raw_type, "UNVERIFIED")

            return {
                "status":    status,
                "line_type": raw_type,
                "carrier":   lti.get("carrier_name") or "",
                "formatted": data.get("national_format") or phone,
            }
        except Exception:
            return {"status": "UNVERIFIED", "line_type": "", "carrier": "", "formatted": phone}

    def validate_batch(self, contacts: list[dict]) -> list[dict]:
        """Add _phone_status and _phone_type to each contact that has a phone number.

        Contacts without a phone number get _phone_status = 'MISSING'.
        """
        phones_to_check = [(i, c) for i, c in enumerate(contacts) if c.get("phone")]
        if not phones_to_check:
            for c in contacts:
                c["_phone_status"] = "MISSING"
                c["_phone_type"]   = ""
            return contacts

        print(f"      Checking {len(phones_to_check)} phone numbers via Twilio Lookup...")
        for i, c in phones_to_check:
            result = self.lookup(c["phone"])
            c["_phone_status"] = result["status"]
            c["_phone_type"]   = result["line_type"]
            if result["formatted"] and result["formatted"] != c["phone"]:
                c["phone"] = result["formatted"]
            time.sleep(0.1)

        for c in contacts:
            if "_phone_status" not in c:
                c["_phone_status"] = "Not validated — dial and see" if c.get("phone") else "MISSING"
                c["_phone_type"]   = ""

        mobile   = sum(1 for c in contacts if c.get("_phone_status") == "MOBILE")
        landline = sum(1 for c in contacts if c.get("_phone_status") == "LANDLINE")
        voip     = sum(1 for c in contacts if c.get("_phone_status") == "VOIP")
        print(f"      Mobile={mobile}  Landline={landline}  VoIP={voip}")

        return contacts
