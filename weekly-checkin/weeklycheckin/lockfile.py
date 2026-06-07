"""A config-path-namespaced lockfile so two concurrent weekly-checkin runs don't both deliver.

The lock path is derived from a hash of the *absolute* config path, so separate config files (or
separate users) on one machine never collide. Acquisition is atomic (``O_CREAT | O_EXCL``).

A stale lock left behind by a crashed run is reclaimed rather than blocking forever: the holder
PID is probed (a dead PID means the run is gone), and a lock older than ``stale_after_seconds`` is
treated as abandoned. ``acquire`` raises ``LockHeld`` only when a live, non-stale run still holds
it. ``pid``/``now``/``is_alive`` are injectable so the logic is unit-tested without real processes.
"""
import hashlib
import os
import tempfile

DEFAULT_STALE_AFTER_SECONDS = 6 * 3600


class LockHeld(RuntimeError):
    pass


def lock_path_for(config_path, *, lock_dir=None):
    digest = hashlib.sha1(os.path.abspath(config_path).encode("utf-8")).hexdigest()[:12]
    return os.path.join(lock_dir or tempfile.gettempdir(), f"weekly-checkin-{digest}.lock")


def acquire(path, *, pid, now, stale_after_seconds=DEFAULT_STALE_AFTER_SECONDS, is_alive=None):
    is_alive = is_alive or _pid_alive
    try:
        _create(path, pid, now)
        return
    except FileExistsError:
        pass

    holder_pid, created_at = _read(path)
    abandoned = (
        holder_pid is None
        or not is_alive(holder_pid)
        or (created_at is not None and now - created_at > stale_after_seconds)
    )
    if not abandoned:
        raise LockHeld(
            f"another weekly-checkin run holds {path} (pid {holder_pid}); "
            "if that process is gone, delete the lockfile and retry"
        )

    # Reclaim the abandoned lock. If a racing run recreates it first, fail loudly rather than
    # stomping its lock.
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass
    try:
        _create(path, pid, now)
    except FileExistsError:
        raise LockHeld(f"another weekly-checkin run reclaimed {path}; retry shortly")


def release(path, *, pid):
    # Only remove the lock if we still own it, so we never delete a reclaimer's lock.
    holder_pid, _ = _read(path)
    if holder_pid is None or holder_pid == pid:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


def _create(path, pid, now):
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(f"{pid}\n{now}\n")


def _read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except FileNotFoundError:
        return None, None
    pid = _to_int(lines[0]) if len(lines) >= 1 else None
    created = _to_float(lines[1]) if len(lines) >= 2 else None
    return pid, created


def _pid_alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _to_int(s):
    try:
        return int(s.strip())
    except (ValueError, AttributeError):
        return None


def _to_float(s):
    try:
        return float(s.strip())
    except (ValueError, AttributeError):
        return None
