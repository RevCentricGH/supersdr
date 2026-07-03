#!/usr/bin/env bash
# Render a weekly-checkin brief .docx from a content JSON.
#
# Thin wrapper over build_docx.py that selects a Python which actually has
# python-docx: it prefers ~/.venv (the same interpreter the disco-deck render.sh
# uses, which also carries Pillow), then falls back to the PATH python3. If
# neither has python-docx it exits with a clear install hint rather than a
# cryptic ImportError mid-run. Mirrors the deck's render.sh pattern (ADR-0008).
#
# Both the import check and the build run with the working directory set to this
# script's own dir, and the JSON/output paths are resolved to absolute first, so
# a stray module in the caller's cwd (e.g. an inspect.py or docx.py in /tmp) can
# never shadow stdlib and break `import docx`. Output still lands where the
# caller asked.
#
# Usage:
#   render.sh content.json "RevCentric Weekly Check-in Brief - <Client> (<YYYY-MM-DD>).docx"
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "$#" -lt 2 ]; then
  echo "usage: render.sh <content.json> <out.docx>" >&2
  exit 2
fi

# Resolve args against the caller's cwd so we can run Python from a neutral dir.
abspath() { case "$1" in /*) printf '%s' "$1" ;; *) printf '%s/%s' "$PWD" "$1" ;; esac; }
CONTENT="$(abspath "$1")"
OUT="$(abspath "$2")"

pick_py() {
  for py in "$HOME/.venv/bin/python3" "$(command -v python3 || true)"; do
    [ -n "$py" ] && [ -x "$py" ] || continue
    if (cd "$DIR" && "$py" -c "import docx") >/dev/null 2>&1; then
      echo "$py"
      return 0
    fi
  done
  return 1
}

PY="$(pick_py)" || {
  echo "render.sh: no Python with python-docx found. Install it, for example:" >&2
  echo "  \"\$HOME/.venv/bin/python3\" -m pip install python-docx" >&2
  exit 1
}

cd "$DIR"
exec "$PY" "$DIR/build_docx.py" "$CONTENT" "$OUT"
