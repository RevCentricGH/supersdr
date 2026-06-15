"""lockfile.py: atomic acquisition, stale-lock reclaim, and config-path namespacing."""
import os

import pytest

from weeklycheckin import lockfile


def test_lock_path_namespaced_by_config_path(tmp_path):
    a = lockfile.lock_path_for("/some/dir/config.json", lock_dir=str(tmp_path))
    b = lockfile.lock_path_for("/other/dir/config.json", lock_dir=str(tmp_path))
    assert a != b
    assert a.endswith(".lock") and b.endswith(".lock")


def test_lock_path_stable_for_same_config(tmp_path):
    a = lockfile.lock_path_for("config.json", lock_dir=str(tmp_path))
    b = lockfile.lock_path_for(os.path.abspath("config.json"), lock_dir=str(tmp_path))
    assert a == b


def test_acquire_then_release(tmp_path):
    path = str(tmp_path / "wc.lock")
    lockfile.acquire(path, pid=111, now=1000.0, is_alive=lambda p: True)
    assert os.path.exists(path)
    lockfile.release(path, pid=111)
    assert not os.path.exists(path)


def test_acquire_blocks_when_live_holder(tmp_path):
    path = str(tmp_path / "wc.lock")
    lockfile.acquire(path, pid=111, now=1000.0, is_alive=lambda p: True)
    with pytest.raises(lockfile.LockHeld):
        lockfile.acquire(path, pid=222, now=1001.0, is_alive=lambda p: True)


def test_acquire_reclaims_dead_holder(tmp_path):
    path = str(tmp_path / "wc.lock")
    lockfile.acquire(path, pid=111, now=1000.0, is_alive=lambda p: True)
    # Holder 111 is gone; a new run reclaims the lock instead of blocking forever.
    lockfile.acquire(path, pid=222, now=1001.0, is_alive=lambda p: p != 111)
    held_pid, _ = lockfile._read(path)
    assert held_pid == 222


def test_acquire_reclaims_age_expired_lock(tmp_path):
    path = str(tmp_path / "wc.lock")
    lockfile.acquire(path, pid=111, now=1000.0, is_alive=lambda p: True)
    # Same live PID, but the lock is older than the stale window: treat it as abandoned.
    lockfile.acquire(
        path, pid=222, now=1000.0 + 10 * 3600, stale_after_seconds=6 * 3600, is_alive=lambda p: True
    )
    held_pid, _ = lockfile._read(path)
    assert held_pid == 222


def test_release_does_not_remove_other_owners_lock(tmp_path):
    path = str(tmp_path / "wc.lock")
    lockfile.acquire(path, pid=111, now=1000.0, is_alive=lambda p: True)
    lockfile.release(path, pid=999)  # not the owner: must be a no-op
    assert os.path.exists(path)
    lockfile.release(path, pid=111)
    assert not os.path.exists(path)
