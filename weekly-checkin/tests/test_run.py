"""run.py end-to-end wiring: dry-run, empty-week notice, delivery routing, and lock contention.

The live digest build (Google Sheets + SmartLead) and the live Docs/Slack/SMTP clients are stubbed
so the orchestration in run.main - validate, lock, build, activity-gate, route, release - is
exercised without credentials or a network, against the same sample fixture the deliver tests use.
"""
import json
import os
import time

import pytest

import run
from weeklycheckin import deliver, lockfile

_HERE = os.path.dirname(os.path.abspath(__file__))


def _sections():
    with open(os.path.join(_HERE, "sample_clients.json"), encoding="utf-8") as fh:
        return json.load(fh)


def _zero_sections():
    return [
        {"client": "Quiet Co", "week": "2026-W22", "calls": 0, "dispositions": {},
         "campaigns": [{"campaign_id": 1, "stats": None}]},
    ]


def _write_config(tmp_path, delivery):
    cfg = {
        "smartlead_api_key": "k",
        "google_sheet_id": "s",
        "google_oauth": {"credentials_file": "c", "token_file": "t"},
        "clients": [{"name": "Acme Co", "rep_tabs": ["Alice"], "smartlead_campaign_ids": [1]}],
        "delivery": delivery,
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return str(path)


@pytest.fixture(autouse=True)
def _stub_digest(monkeypatch):
    # Default: an active digest. Individual tests override via monkeypatch when they need zeros.
    monkeypatch.setattr(run, "_build_digest", lambda config, week: (_sections(), object()))


def test_dry_run_prints_digest_and_skips_delivery(tmp_path, capsys, monkeypatch):
    posts = []
    monkeypatch.setattr(deliver, "_default_http_post", lambda: lambda *a: posts.append(a))
    cfg = _write_config(tmp_path, {"type": "slack", "slack_webhook_env": "WC_HOOK"})

    run.main(["--week", "2026-W22", "--config", cfg, "--dry-run"])

    out = capsys.readouterr()
    assert "Acme Co" in out.out
    assert posts == []
    # Dry run takes no lock.
    assert not os.path.exists(lockfile.lock_path_for(cfg))


def test_empty_week_delivers_no_activity_notice(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(run, "_build_digest", lambda config, week: (_zero_sections(), object()))
    posts = []

    class _Resp:
        status_code = 200

    monkeypatch.setattr(deliver, "_default_http_post", lambda: lambda url, payload, t: posts.append((url, payload)) or _Resp())
    monkeypatch.setenv("WC_HOOK", "https://hooks/X")
    cfg = _write_config(tmp_path, {"type": "slack", "slack_webhook_env": "WC_HOOK"})

    run.main(["--week", "2026-W22", "--config", cfg])

    err = capsys.readouterr().err
    assert "no call or campaign activity" in err
    assert len(posts) == 1
    assert "no call or campaign activity this week" in posts[0][1]["text"]
    assert "Quiet Co" in posts[0][1]["text"]
    assert not os.path.exists(lockfile.lock_path_for(cfg))  # lock released in finally


def test_live_slack_delivery_routes_and_releases_lock(tmp_path, monkeypatch):
    posts = []

    class _Resp:
        status_code = 200

    monkeypatch.setattr(deliver, "_default_http_post", lambda: lambda url, payload, t: posts.append((url, payload)) or _Resp())
    monkeypatch.setenv("WC_HOOK", "https://hooks/X")
    cfg = _write_config(tmp_path, {"type": "slack", "slack_webhook_env": "WC_HOOK"})

    run.main(["--week", "2026-W22", "--config", cfg])

    assert len(posts) == 1
    assert "Acme Co" in posts[0][1]["text"]
    assert not os.path.exists(lockfile.lock_path_for(cfg))


def test_live_doc_delivery_appends_run_id_section(tmp_path, monkeypatch):
    appended = []
    monkeypatch.setattr(run, "_doc_appender", lambda creds: lambda doc_id, text: appended.append((doc_id, text)))
    cfg = _write_config(tmp_path, {"type": "google_doc", "target": "doc-9"})

    run.main(["--week", "2026-W22", "--config", cfg])

    assert len(appended) == 1
    doc_id, text = appended[0]
    assert doc_id == "doc-9"
    assert "Acme Co" in text
    assert "weekly-checkin 2026-" in text  # run_id heading present
    assert not os.path.exists(lockfile.lock_path_for(cfg))


def test_invalid_delivery_type_exits_before_locking(tmp_path):
    cfg = _write_config(tmp_path, {"type": "bogus"})
    with pytest.raises(SystemExit) as exc:
        run.main(["--week", "2026-W22", "--config", cfg])
    assert "bogus" in str(exc.value)
    assert not os.path.exists(lockfile.lock_path_for(cfg))


def test_concurrent_run_is_refused(tmp_path, monkeypatch):
    cfg = _write_config(tmp_path, {"type": "google_doc", "target": "doc-9"})
    monkeypatch.setattr(run, "_doc_appender", lambda creds: lambda *a: None)
    lock_path = lockfile.lock_path_for(cfg)
    # A live holder is already running.
    lockfile.acquire(lock_path, pid=os.getpid(), now=time.time(), is_alive=lambda p: True)
    try:
        with pytest.raises(SystemExit) as exc:
            run.main(["--week", "2026-W22", "--config", cfg])
        assert "holds" in str(exc.value)
    finally:
        lockfile.release(lock_path, pid=os.getpid())
