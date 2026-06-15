#!/usr/bin/env python3
"""Guard: every action type in apollo-campaign-builder's WORKFLOWS must be
documented as a bold bullet in the SKILL.md Step 3 action list.

This stops doc drift: if a new action type is added to workflow_builder.WORKFLOWS
but the Step 3 walkthrough is not updated, this guard fails and names the
missing type.

Run directly:  python3 tests/test_campaign_builder_guard.py
Also invoked by scripts/validate_skills.py. Stdlib only, no pytest.
"""
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(REPO_ROOT, "apollo-campaign-builder")

sys.path.insert(0, SKILL_DIR)
import workflow_builder  # noqa: E402  (sibling skill dir, added to sys.path above)


def collect_action_types():
    """Every action["type"] across all WORKFLOWS[*]["actions"] lists, first-seen
    order. The top-level "Disposition Change" trigger lives in trigger["type"],
    not in an actions list, so it is excluded by construction."""
    types = []
    for workflow in workflow_builder.WORKFLOWS.values():
        for action in workflow["actions"]:
            t = action["type"]
            if t not in types:
                types.append(t)
    return types


def step3_bullet_labels():
    """Bold bullet labels (`- **Label**:`) inside the Step 3 slice of SKILL.md."""
    skill_path = os.path.join(SKILL_DIR, "SKILL.md")
    text = open(skill_path, encoding="utf-8").read()
    start = text.find("## Step 3")
    end = text.find("## Step 4")
    if start == -1 or end == -1 or end <= start:
        raise SystemExit(
            "Guard FAILED: could not slice SKILL.md between '## Step 3' and '## Step 4'"
        )
    step3 = text[start:end]
    if not step3.strip():
        raise SystemExit("Guard FAILED: Step 3 slice is empty")
    return set(re.findall(r"^\s*-\s+\*\*(.+?)\*\*", step3, re.MULTILINE))


def main():
    action_types = collect_action_types()
    if not action_types:
        raise SystemExit("Guard FAILED: no action types found in WORKFLOWS")

    labels = step3_bullet_labels()
    missing = [t for t in action_types if t not in labels]
    if missing:
        raise SystemExit(
            "Guard FAILED: Step 3 is missing a bullet for action type(s): "
            + ", ".join(missing)
        )
    print(f"Guard OK: all {len(action_types)} WORKFLOWS action types documented in Step 3.")


if __name__ == "__main__":
    main()
