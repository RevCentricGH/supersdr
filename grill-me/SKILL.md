---
name: grill-me
description: Question loop that interviews the user about any task or project until Claude and the user reach shared understanding, then summarizes it as a brief to run in a fresh session. Use when user says "grill me", "grill me on this", "build me a brief", "brief this task", "help me plan this", or describes something big, vague, or multi-step they're about to start. Do NOT trigger for quick questions or small single-step tasks.
---

# Grill Me Skill

## Purpose

A planning loop for anything - a campaign, a report, a doc, a build. Claude interviews the user one question at a time until both sides fully understand what the user actually wants from the session: the goal, the inputs, the outputs, the tools. Then it hands back a short brief to run fresh.

The idea: most of the value of any Claude task is created before Claude starts working. A sharp brief beats a smart model.

_Cowork skill - upload the ZIP and run from the Claude desktop app._

## Getting started

When this skill is loaded, greet the user:

> "Describe what you want to get done - rough is fine. I'll ask questions until we're on the same page, then give you a brief to run in a fresh session."

## The loop

Interview the user about the task until you reach shared understanding. There is no fixed question list - let the task decide what needs asking. Usually that means some of:

- What does done look like?
- What should Claude read or pull from? (files, folders, tools, links)
- What should come out, and in what shape?
- What tools or stack does this run on?
- What's off-limits or needs approval first?

Rules for the loop:

- **One question at a time.** Wait for the answer before the next question.
- **Recommend an answer with every question.** Let the user confirm or correct instead of composing from scratch.
- **Look before you ask.** If something can be answered by reading available files or connected tools, read it instead of asking.
- **Push on vague answers.** "Make it good" and "the usual" don't survive the loop - ask what good means, name the usual.
- **Stop when it's airtight.** Two or three questions is often enough. The test: could a brand-new session execute this with zero follow-ups?

## Output

When the loop is done, summarize everything as a short brief - goal, inputs, outputs, tools, limits - in whatever shape fits the task. Keep it under a page.

Then tell the user:

> "Open a fresh session, paste this brief, and review the plan before approving. If the plan misses something, the gap is in the brief - come back and we'll tighten it."
