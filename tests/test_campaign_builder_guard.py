#!/usr/bin/env python3
"""Guards for the Apollo skill pair (apollo-account-setup + apollo-campaign-builder).

1. Every action type in WORKFLOWS must be documented as a bold bullet in the
   SKILL.md Step 3 action list.
2. Every workflow trigger must filter on a real DISPOSITION, never on a contact
   stage. This is the regression that shipped once already: the guide told the
   agent to pick "Meeting Scheduled" and "Connect Incomplete" out of a contact
   stage picker. Neither is a stage, so the workflow could never leave Draft.
3. No workflow may carry an "Update Contact Stage" action. Stages are owned by
   the disposition triggers; a stage write here duplicates them and can re-fire
   the workflow against its own output.
4. Every trigger in triggers_builder must reference a real disposition and a
   real stage, and every disposition must be mapped exactly once.

Run directly:  python3 tests/test_campaign_builder_guard.py
Also invoked by scripts/validate_skills.py. Stdlib only, no pytest.
"""
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(REPO_ROOT, "apollo-campaign-builder")
SETUP_DIR = os.path.join(REPO_ROOT, "apollo-account-setup")

sys.path.insert(0, SKILL_DIR)
sys.path.insert(0, SETUP_DIR)
import workflow_builder  # noqa: E402  (sibling skill dir, added to sys.path above)
import dispositions_builder  # noqa: E402
import stages_builder  # noqa: E402
import triggers_builder  # noqa: E402

DISPOSITION_NAMES = {d["name"] for d in dispositions_builder.DISPOSITIONS}
STAGE_NAMES = set(stages_builder.STAGES)


def collect_action_types():
    """Every action["type"] across all WORKFLOWS[*]["actions"] lists, first-seen
    order. The top-level "Call Logged" trigger lives in trigger["type"],
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


def check_workflow_triggers():
    """Each workflow must fire on "Call Logged" and filter on a real disposition.

    A trigger value that is a contact stage rather than a disposition is the
    exact bug this guard exists to stop.
    """
    problems = []
    for key, workflow in workflow_builder.WORKFLOWS.items():
        trigger = workflow["trigger"]

        if trigger.get("type") != "Call Logged":
            problems.append(
                f"WORKFLOWS[{key}] trigger type is {trigger.get('type')!r}; "
                "Apollo's event is 'Call Logged' (there is no disposition-change event, "
                "and 'Contact updated' targets stages, not dispositions)"
            )

        disposition = trigger.get("disposition")
        if disposition not in DISPOSITION_NAMES:
            problems.append(
                f"WORKFLOWS[{key}] filters on {disposition!r}, which is not in "
                "dispositions_builder.DISPOSITIONS"
                + (
                    " (it is a contact stage — workflows filter on dispositions)"
                    if disposition in STAGE_NAMES
                    else ""
                )
            )

        if not trigger.get("source_sequence"):
            problems.append(
                f"WORKFLOWS[{key}] has no source_sequence; without it the workflow "
                "fires on every logged call in the workspace"
            )
    return problems


def check_no_stage_writes():
    """Workflows route sequences. Stage movement belongs to the triggers."""
    problems = []
    for key, workflow in workflow_builder.WORKFLOWS.items():
        for action in workflow["actions"]:
            if action["type"] == "Update Contact Stage":
                problems.append(
                    f"WORKFLOWS[{key}] has an 'Update Contact Stage' action "
                    f"(stage {action.get('stage')!r}). Stages are owned by "
                    "triggers_builder.TRIGGERS; remove the action."
                )
    return problems


def check_trigger_map():
    """Every disposition maps to exactly one existing stage."""
    problems = []
    seen = []
    for entry in triggers_builder.TRIGGERS:
        disposition, stage = entry["disposition"], entry["stage"]
        if disposition not in DISPOSITION_NAMES:
            problems.append(f"TRIGGERS references unknown disposition {disposition!r}")
        if stage not in STAGE_NAMES:
            problems.append(f"TRIGGERS references unknown stage {stage!r}")
        if disposition in seen:
            problems.append(f"TRIGGERS maps {disposition!r} more than once")
        seen.append(disposition)

    for unmapped in sorted(DISPOSITION_NAMES - set(seen)):
        problems.append(f"TRIGGERS leaves disposition {unmapped!r} unmapped")
    return problems


def main():
    action_types = collect_action_types()
    if not action_types:
        raise SystemExit("Guard FAILED: no action types found in WORKFLOWS")

    labels = step3_bullet_labels()
    problems = [
        f"Step 3 is missing a bullet for action type: {t}"
        for t in action_types
        if t not in labels
    ]
    problems += check_workflow_triggers()
    problems += check_no_stage_writes()
    problems += check_trigger_map()

    if problems:
        raise SystemExit(
            "Guard FAILED:\n  - " + "\n  - ".join(problems)
        )

    print(
        f"Guard OK: {len(action_types)} action types documented; "
        f"{len(workflow_builder.WORKFLOWS)} workflow triggers filter on real dispositions; "
        f"{len(triggers_builder.TRIGGERS)} disposition->stage triggers resolve."
    )


if __name__ == "__main__":
    main()
