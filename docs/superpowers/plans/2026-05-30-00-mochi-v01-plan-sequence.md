# Mochi v0.1 Plan Sequence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide the execution order for Mochi Robot Brain v0.1 implementation plans.

**Architecture:** v0.1 is a text-only robot brain with fake adapters, local SQLite memory, and a Typer/Rich CLI. The conversation brain talks through interfaces so fake navigation, fake battery, and fake LLM implementations can be replaced later without rewriting core behavior.

**Tech Stack:** Python 3.11+, Typer, Rich, Pydantic, PyYAML, SQLite, pytest, ruff.

---

## Execution Order

Run these plans one at a time. After each plan, run `pytest` and `ruff check .`.

1. `docs/superpowers/plans/2026-05-30-01-bootstrap-repo.md`
2. `docs/superpowers/plans/2026-05-30-02-agents-instructions.md`
3. `docs/superpowers/plans/2026-05-30-03-config-loading.md`
4. `docs/superpowers/plans/2026-05-30-04-robot-state.md`
5. `docs/superpowers/plans/2026-05-30-05-fake-navigation.md`
6. `docs/superpowers/plans/2026-05-30-06-sqlite-memory.md`
7. `docs/superpowers/plans/2026-05-30-07-llm-client-abstraction.md`
8. `docs/superpowers/plans/2026-05-30-08-personality-prompt-builder.md`
9. `docs/superpowers/plans/2026-05-30-09-action-router.md`
10. `docs/superpowers/plans/2026-05-30-10-conversation-engine.md`
11. `docs/superpowers/plans/2026-05-30-11-cli-chat-app.md`
12. `docs/superpowers/plans/2026-05-30-12-behavior-planner.md`
13. `docs/superpowers/plans/2026-05-30-13-readme-and-v01-acceptance.md`

## Global v0.1 Boundaries

- [x] Keep v0.1 text-only.
- [x] Do not add hardware control, ROS, Gazebo, camera, microphone, real face recognition, or Home Assistant.
- [x] Use fake adapters for navigation, sensors, battery, and LLM tests.
- [x] Store local memories only when explicit remember commands are used.
- [x] Keep privacy mode quiet: no proactive speech while privacy mode is enabled.
- [x] Do not require an OpenAI API key for tests.

## Final Verification

- [x] Run: `pytest`
- [x] Expected: all tests pass.
- [x] Run: `ruff check .`
- [x] Expected: all checks pass.
- [x] Run: `mochi --help`
- [x] Expected: help shows `chat`, `state`, `memories`, `forget`, and `privacy`.
- [x] Run: `mochi chat`
- [x] Expected: terminal chat starts and exits cleanly with `exit` or `quit`.
