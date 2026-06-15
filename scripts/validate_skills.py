#!/usr/bin/env python3
"""Validate every skill folder under skills/.

Run from the repo root: `python3 scripts/validate_skills.py`.
Exits non-zero with a list of problems if anything is wrong.

Checks:
  1. No gitignored/internal files (DEV_STATUS.md, .internal, __pycache__) are committed.
  2. Every folder under skills/ with a SKILL.md has frontmatter whose `name:` matches the
     folder and whose `description:` is non-empty, has a space after the colon (YAML
     drops the key without it), and is at most 1024 chars (Claude's skill upload limit).
  3. At least one skill exists under skills/ (guards against running from the wrong cwd).
  4. No SKILL.md lives outside skills/ (a skill dropped at root or any other depth fails).
"""
import os
import sys
import re
import subprocess
from pathlib import Path

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

    # 2. Every folder under skills/ with a SKILL.md must be a valid skill.
    if not os.path.isdir("skills"):
        print("Validation FAILED:\n\n  - skills/ directory not found (run from the repo root)")
        sys.exit(1)
    skill_count = 0
    for entry in sorted(os.listdir("skills")):
        folder = os.path.join("skills", entry)
        skill = os.path.join(folder, "SKILL.md")
        if not (os.path.isdir(folder) and os.path.isfile(skill)):
            continue
        skill_count += 1
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

    # 3. Zero skills found means the scan looked at the wrong place; never pass silently.
    if skill_count == 0:
        errors.append("no skills found under skills/ (every skill must live at skills/<name>/SKILL.md)")

    # 4. No SKILL.md may live outside skills/. Skip the gitignored internal roots
    #    (.internal helper, etc.) - they are expected on disk but never committed,
    #    and check #1 above already guards against them being tracked.
    skip_roots = {".git", ".github"} | {f.rstrip("/") for f in FORBIDDEN}
    for p in sorted(Path(".").rglob("SKILL.md")):
        parts = p.parts
        if parts[0] in skip_roots:
            continue
        if parts[0] != "skills":
            errors.append(f"misplaced SKILL.md outside skills/: {p}")

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
