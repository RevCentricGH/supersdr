"""Deliver the rendered weekly digest to a configured destination.

One join point, ``deliver``, switches on ``delivery.type`` (``google_doc`` | ``slack`` | ``email``)
and routes to the matching backend after validating the delivery config. Validation failures raise
``SystemExit`` with a bounded, human-readable message (no traceback) so a misconfigured cron job
logs one clear line instead of a stack dump.

Secrets are never read from config. The Slack webhook URL and the SMTP password come from
environment variables *named* in config (``slack_webhook_env`` / ``smtp_password_env``), so the
committed config carries no credentials and a redacted error never leaks one.

The side-effecting pieces (the Docs append, the HTTP POST, the SMTP send) are injected, so the
backends are exercised in tests with fakes and ``run.py`` wires the live clients.
"""
import os

SUPPORTED_TYPES = ("google_doc", "slack", "email")
DEFAULT_EMAIL_SUBJECT = "weekly-checkin digest"

# The fields each backend needs in the `delivery` block. `target` is the Google Doc id for
# google_doc and the recipient address for email; Slack uses `slack_webhook_env`, not `target`.
_REQUIRED_FIELDS = {
    "google_doc": ("target",),
    "slack": ("slack_webhook_env",),
    "email": (
        "target",
        "from_address",
        "smtp_host",
        "smtp_port",
        "smtp_user",
        "smtp_password_env",
    ),
}


def _fail(message):
    raise SystemExit(f"weekly-checkin delivery: {message}")


def validate_delivery_config(delivery):
    """Structural validation of the `delivery` block (no env-var resolution). Returns the
    delivery type on success; raises SystemExit with a bounded message on any problem."""
    if not isinstance(delivery, dict) or not delivery:
        _fail("config has no 'delivery' block; add delivery.type (google_doc | slack | email)")
    dtype = delivery.get("type")
    if not dtype:
        _fail("delivery.type is missing; set it to one of: " + ", ".join(SUPPORTED_TYPES))
    if dtype not in SUPPORTED_TYPES:
        _fail(
            f"delivery.type '{dtype}' is not supported; use one of: " + ", ".join(SUPPORTED_TYPES)
        )
    missing = [f for f in _REQUIRED_FIELDS[dtype] if not delivery.get(f)]
    if missing:
        _fail(
            f"delivery.type '{dtype}' is missing required field(s): " + ", ".join(missing)
        )
    return dtype


def deliver(
    digest,
    delivery,
    *,
    run_id,
    doc_appender=None,
    http_post=None,
    smtp_factory=None,
    env=None,
):
    """Validate the delivery config and route the digest to the matching backend."""
    dtype = validate_delivery_config(delivery)
    if dtype == "google_doc":
        if doc_appender is None:
            _fail("internal: no Google Docs appender wired for google_doc delivery")
        return deliver_to_doc(digest, delivery, run_id=run_id, doc_appender=doc_appender)
    if dtype == "slack":
        return deliver_to_slack(digest, delivery, http_post=http_post, env=env)
    return deliver_to_email(digest, delivery, smtp_factory=smtp_factory, env=env)


def deliver_to_doc(digest, delivery, *, run_id, doc_appender):
    """Append the digest to a Google Doc under a heading tagged with `run_id`, so each append is
    an independently removable section (two same-day runs produce two distinct headings)."""
    section = f"\n\n=== weekly-checkin {run_id} ===\n{digest}\n"
    doc_appender(delivery["target"], section)
    return run_id


def deliver_to_slack(digest, delivery, *, http_post=None, env=None):
    """POST the digest to the Slack incoming webhook named by `delivery.slack_webhook_env`."""
    webhook = _require_env(env, delivery["slack_webhook_env"], "Slack incoming webhook URL")
    post = http_post or _default_http_post()
    resp = post(webhook, {"text": digest}, 30)
    status = getattr(resp, "status_code", None)
    if status is None or not (200 <= status < 300):
        body = _redact(getattr(resp, "text", "") or "")
        _fail(f"Slack webhook returned HTTP {status}: {body}")
    return status


def deliver_to_email(digest, delivery, *, smtp_factory=None, env=None):
    """Send the digest as an email over SMTP. Host/port/user come from config; the password comes
    from the env var named by `delivery.smtp_password_env`."""
    password = _require_env(env, delivery["smtp_password_env"], "SMTP password")
    message = _build_email(
        delivery["from_address"],
        delivery["target"],
        delivery.get("subject", DEFAULT_EMAIL_SUBJECT),
        digest,
    )
    factory = smtp_factory or _default_smtp_factory()
    client = factory(delivery["smtp_host"], int(delivery["smtp_port"]), 30)
    try:
        client.starttls()
        client.login(delivery["smtp_user"], password)
        client.send_message(message)
    finally:
        client.quit()
    return delivery["target"]


def _require_env(env, var_name, purpose):
    value = (os.environ if env is None else env).get(var_name)
    if not value:
        _fail(
            f"environment variable '{var_name}' ({purpose}) is unset or empty; "
            "export it before delivering"
        )
    return value


def _build_email(from_address, to_address, subject, body):
    from email.message import EmailMessage

    message = EmailMessage()
    message["From"] = from_address
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)
    return message


def _redact(text, limit=200):
    text = " ".join(text.split())
    return text[:limit] + ("..." if len(text) > limit else "")


def _default_http_post():
    def post(url, payload, timeout):
        import requests

        return requests.post(url, json=payload, timeout=timeout)

    return post


def _default_smtp_factory():
    def factory(host, port, timeout):
        import smtplib

        return smtplib.SMTP(host, port, timeout=timeout)

    return factory
