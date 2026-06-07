"""deliver.py: config-validation matrix plus one integration test per backend against fixtures.

The validation matrix asserts a bounded SystemExit (no traceback) for every misconfiguration the
plan calls out. The backend tests inject fakes for the side-effecting pieces (Docs append, HTTP
POST, SMTP) so the routing, run_id heading, env-var indirection, and error redaction are exercised
without a network or live credentials.
"""
import json
import os

import pytest

from weeklycheckin import deliver
from weeklycheckin.digest_builder import digest_has_activity, render_digest

_HERE = os.path.dirname(os.path.abspath(__file__))


def _sections():
    with open(os.path.join(_HERE, "sample_clients.json"), encoding="utf-8") as fh:
        return json.load(fh)


def _digest():
    return render_digest(_sections())


# --- config validation matrix -------------------------------------------------------------

def test_missing_delivery_block_exits():
    with pytest.raises(SystemExit) as exc:
        deliver.validate_delivery_config(None)
    assert "delivery" in str(exc.value)


def test_missing_type_exits():
    with pytest.raises(SystemExit) as exc:
        deliver.validate_delivery_config({"target": "x"})
    assert "delivery.type" in str(exc.value)


def test_unsupported_type_exits_with_supported_list():
    with pytest.raises(SystemExit) as exc:
        deliver.validate_delivery_config({"type": "carrier_pigeon"})
    msg = str(exc.value)
    assert "carrier_pigeon" in msg
    assert "google_doc" in msg and "slack" in msg and "email" in msg


def test_google_doc_missing_target_exits():
    with pytest.raises(SystemExit) as exc:
        deliver.validate_delivery_config({"type": "google_doc"})
    assert "target" in str(exc.value)


def test_slack_missing_webhook_env_exits():
    with pytest.raises(SystemExit) as exc:
        deliver.validate_delivery_config({"type": "slack"})
    assert "slack_webhook_env" in str(exc.value)


def test_email_missing_fields_names_each_missing():
    with pytest.raises(SystemExit) as exc:
        deliver.validate_delivery_config({"type": "email", "target": "to@x.com"})
    msg = str(exc.value)
    for field in ("from_address", "smtp_host", "smtp_port", "smtp_user", "smtp_password_env"):
        assert field in msg


def test_valid_config_returns_type():
    assert deliver.validate_delivery_config({"type": "google_doc", "target": "doc1"}) == "google_doc"


def test_no_traceback_only_systemexit():
    # SystemExit (not a bare exception) is what argparse/sys.exit use: Python prints the message,
    # not a stack trace. Confirm validation never raises a different exception type.
    with pytest.raises(SystemExit):
        deliver.validate_delivery_config({"type": "nope"})


# --- env-var resolution (resolved at send time, not during structural validation) ----------

def test_slack_unset_env_exits():
    cfg = {"type": "slack", "slack_webhook_env": "WC_SLACK_HOOK"}
    with pytest.raises(SystemExit) as exc:
        deliver.deliver(_digest(), cfg, run_id="rid", env={})
    assert "WC_SLACK_HOOK" in str(exc.value)


def test_slack_empty_env_exits():
    cfg = {"type": "slack", "slack_webhook_env": "WC_SLACK_HOOK"}
    with pytest.raises(SystemExit) as exc:
        deliver.deliver(_digest(), cfg, run_id="rid", env={"WC_SLACK_HOOK": ""})
    assert "WC_SLACK_HOOK" in str(exc.value)


def test_email_unset_password_env_exits():
    cfg = {
        "type": "email",
        "target": "to@x.com",
        "from_address": "from@x.com",
        "smtp_host": "smtp.x.com",
        "smtp_port": 587,
        "smtp_user": "from@x.com",
        "smtp_password_env": "WC_SMTP_PW",
    }
    with pytest.raises(SystemExit) as exc:
        deliver.deliver(_digest(), cfg, run_id="rid", env={})
    assert "WC_SMTP_PW" in str(exc.value)


# --- backend integration against the fixture digest ---------------------------------------

def test_doc_backend_appends_run_id_tagged_section():
    appended = []
    cfg = {"type": "google_doc", "target": "doc-123"}
    digest = _digest()
    rid = "2026-06-06T09:00:00-a3f2"
    out = deliver.deliver(
        digest, cfg, run_id=rid, doc_appender=lambda doc_id, text: appended.append((doc_id, text))
    )
    assert out == rid
    assert len(appended) == 1
    doc_id, text = appended[0]
    assert doc_id == "doc-123"
    assert rid in text          # the unique heading marker makes the append reversible
    assert "Acme Co" in text    # and the digest body is carried through


def test_slack_backend_posts_digest_as_text():
    posts = []

    class _Resp:
        status_code = 200

    def fake_post(url, payload, timeout):
        posts.append((url, payload, timeout))
        return _Resp()

    cfg = {"type": "slack", "slack_webhook_env": "WC_SLACK_HOOK"}
    deliver.deliver(
        _digest(), cfg, run_id="rid", http_post=fake_post, env={"WC_SLACK_HOOK": "https://hooks/X"}
    )
    assert len(posts) == 1
    url, payload, _ = posts[0]
    assert url == "https://hooks/X"
    assert "Acme Co" in payload["text"]


def test_slack_non_2xx_exits_with_redacted_body_and_no_webhook_leak():
    class _Resp:
        status_code = 403
        text = "invalid_token\nsecret-internal-detail " + "x" * 500

    cfg = {"type": "slack", "slack_webhook_env": "WC_SLACK_HOOK"}
    with pytest.raises(SystemExit) as exc:
        deliver.deliver(
            _digest(),
            cfg,
            run_id="rid",
            http_post=lambda *a: _Resp(),
            env={"WC_SLACK_HOOK": "https://hooks/SECRET-URL"},
        )
    msg = str(exc.value)
    assert "403" in msg
    assert "SECRET-URL" not in msg          # the webhook URL never appears in the error
    assert len(msg) < 400                    # the response body is bounded, not dumped whole


def test_email_backend_sends_message_with_subject_and_body():
    sent = {}

    class _SMTP:
        def __init__(self):
            self.started_tls = False

        def starttls(self):
            self.started_tls = True

        def login(self, user, password):
            sent["auth"] = (user, password)

        def send_message(self, message):
            sent["message"] = message

        def quit(self):
            sent["quit"] = True

    smtp = _SMTP()
    cfg = {
        "type": "email",
        "target": "client@acme.com",
        "from_address": "reports@agency.com",
        "subject": "Weekly check-in",
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_user": "reports@agency.com",
        "smtp_password_env": "WC_SMTP_PW",
    }
    out = deliver.deliver(
        _digest(),
        cfg,
        run_id="rid",
        smtp_factory=lambda host, port, timeout: smtp,
        env={"WC_SMTP_PW": "app-password"},
    )
    assert out == "client@acme.com"
    assert smtp.started_tls is True
    assert sent["auth"] == ("reports@agency.com", "app-password")
    assert sent["quit"] is True
    message = sent["message"]
    assert message["To"] == "client@acme.com"
    assert message["From"] == "reports@agency.com"
    assert message["Subject"] == "Weekly check-in"
    assert "Acme Co" in message.get_content()


def test_email_quits_even_when_send_fails():
    class _SMTP:
        def __init__(self):
            self.quit_called = False

        def starttls(self):
            pass

        def login(self, user, password):
            pass

        def send_message(self, message):
            raise RuntimeError("smtp boom")

        def quit(self):
            self.quit_called = True

    smtp = _SMTP()
    cfg = {
        "type": "email",
        "target": "to@x.com",
        "from_address": "from@x.com",
        "smtp_host": "smtp.x.com",
        "smtp_port": 587,
        "smtp_user": "from@x.com",
        "smtp_password_env": "WC_SMTP_PW",
    }
    with pytest.raises(RuntimeError):
        deliver.deliver(
            _digest(),
            cfg,
            run_id="rid",
            smtp_factory=lambda *a: smtp,
            env={"WC_SMTP_PW": "pw"},
        )
    assert smtp.quit_called is True


# --- empty-digest guard --------------------------------------------------------------------

def test_digest_has_activity_true_for_fixture():
    assert digest_has_activity(_sections()) is True


def test_digest_has_activity_false_for_all_zero_week():
    zeroed = [
        {"client": "Quiet Co", "week": "2026-W23", "calls": 0, "dispositions": {},
         "campaigns": [{"campaign_id": 1, "stats": None}]},
    ]
    assert digest_has_activity(zeroed) is False
