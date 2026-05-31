# Agent Instructions

## Previous Work Memory

Use `memory_work/` for dated summaries of completed work sessions.

When asked to `add to memory_work`, create or update:

```text
memory_work/previous_work_MM_DD_YY.md
```

Keep entries useful for future agents: branch, changed files, commands, verification, bugs, fixes, follow-ups, and decisions. Never include secrets or credentials. Create the directory if it does not already exist.

## Lessons Learned

When a mistake, recurring issue, or preventable trap is discovered, append exactly one CSV row to `docs/lessons_learned/lessons.md`.

Keep lessons minimal:

```csv
"Problem: one-line problem","Solution: one-line solution"
```

Create the directory and file if they do not already exist. Never include secrets or credentials.
