#!/usr/bin/env python3
"""Validate every top-level skill folder.

Run from the repo root: `python3 scripts/validate_skills.py`.
Exits non-zero with a list of problems if anything is wrong.

Checks:
  1. No gitignored/internal files (DEV_STATUS.md, .internal, __pycache__) are committed.
  2. Every top-level folder with a SKILL.md has frontmatter whose `name:` matches the
     folder and whose `description:` is non-empty, has a space after the colon (YAML
     drops the key without it), and is at most 1024 chars (Claude's skill upload limit).
"""
import os
import sys
import re
import subprocess

FORBIDDEN = ["DEV_STATUS.md", ".internal"]


def main():
    errors = []

    # 1. No gitignored/internal files should ever be committed. Check what git
    #    tracks (staged or committed), not what merely sits on disk — gitignored
    #    files like DEV_STATUS.md are expected in the local working tree.
    tracked = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True
    ).stdout.splitlines()
    for f in FORBIDDEN:
        prefix = f.rstrip("/") + "/"
        if any(t == f or t.startswith(prefix) for t in tracked):
            errors.append(f"Forbidden file committed: {f} (this should never be in the repo)")
    for t in tracked:
        if "__pycache__" in t.split("/"):
            errors.append(f"__pycache__ committed: {t}")

    # 2. Every top-level folder with a SKILL.md must be a valid skill.
    for entry in sorted(os.listdir(".")):
        skill = os.path.join(entry, "SKILL.md")
        if not (os.path.isdir(entry) and os.path.isfile(skill)):
            continue
        text = open(skill, encoding="utf-8").read()
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
        if not m:
            errors.append(f"{skill}: missing YAML frontmatter (--- ... ---) at top")
            continue
        fm = m.group(1)
        for key in ("name", "description"):
            if re.search(rf"^{key}:\S", fm, re.MULTILINE):
                errors.append(f"{skill}: '{key}:' needs a space after the colon (YAML drops the key without it)")
        name = re.search(r"^name:\s+(.+)$", fm, re.MULTILINE)
        desc = re.search(r"^description:\s+(.+)$", fm, re.MULTILINE)
        if not name or not name.group(1).strip():
            errors.append(f"{skill}: frontmatter is missing a non-empty 'name:'")
        elif name.group(1).strip() != entry:
            errors.append(f"{skill}: frontmatter name '{name.group(1).strip()}' does not match folder '{entry}'")
        if not desc or not desc.group(1).strip():
            errors.append(f"{skill}: frontmatter is missing a non-empty 'description:'")
        elif len(desc.group(1).strip()) > 1024:
            errors.append(f"{skill}: description is {len(desc.group(1).strip())} chars (Claude skill upload limit is 1024)")

    if errors:
        print("Validation FAILED:\n")
        for e in errors:
            print("  - " + e)
        sys.exit(1)

    # apollo-campaign-builder doc-drift guard: every WORKFLOWS action type must
    # be documented in the SKILL.md Step 3 list. Run in this same interpreter.
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    guard = os.path.join(repo_root, "tests", "test_campaign_builder_guard.py")
    subprocess.run([sys.executable, guard], check=True)

    print("All skills valid.")


if __name__ == "__main__":
    main()
