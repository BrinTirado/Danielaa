# AGENTS Instructions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `AGENTS.md` the persistent coding contract for Mochi v0.1.

**Architecture:** Repo guidance should be concise, enforce v0.1 boundaries, and document privacy, testing, and fake-adapter rules. It should not introduce runtime behavior.

**Tech Stack:** Markdown, pytest, ruff.

---

### Task 1: Expand Repo Guidance

**Files:**
- Modify: `AGENTS.md`

- [x] **Step 1: Replace or expand `AGENTS.md` with project rules**

Use this content structure:

````markdown
# AGENTS.md

## Project

This repo builds Mochi, a software-first robot brain for a future home robot.

The current phase is software-only. Do not implement real robot hardware, ROS, cameras, microphones, or motors unless the task explicitly asks for it.

## Current target

Build v0.1:
- Text-only conversation
- Personality profile
- Local memory
- Fake robot state
- Fake actions
- Fake navigation
- Privacy mode
- Tests

## Development rules

- Prefer simple, readable Python.
- Keep modules small.
- Use interfaces/adapters so fake hardware can later be replaced by real hardware.
- Do not hardcode secrets.
- Read configuration from YAML and environment variables.
- Store local memory in SQLite.
- Include tests for new behavior.
- Run tests before claiming completion.
- Do not add heavy ML, robotics, or camera dependencies in v0.1.
- Do not implement ROS in v0.1.

## Commands

Use these commands when available:

```bash
pytest
ruff check .
ruff format .
```

## Safety and privacy rules

- Do not store private information unless the user explicitly asks Mochi to remember it.
- Add a way to list and delete memories.
- Privacy mode must suppress proactive conversation.
- Unknown people should not be enrolled or remembered automatically.

## Architecture rules

The conversation system must not directly control hardware.

Correct:

```python
action_router.execute(ActionCommand(type="move", payload={"room": "kitchen"}))
```

Incorrect:

```python
motor.left_wheel.forward()
```

Use fake adapters in v0.1:
- FakeNavigator
- FakeBattery
- FakeSensors
- FakeLLM for tests

Later adapters may include:
- OpenAILLM
- WebcamCamera
- ROSNavigator
- HomeAssistantClient
````

- [x] **Step 2: Verify expected guidance is present**

Run: `grep -E "No|ROS|Privacy|FakeNavigator|pytest|ruff" AGENTS.md`

Expected: matching lines for v0.1 boundaries, privacy, fake adapters, and commands.

- [x] **Step 3: Run regression checks**

Run: `pytest`

Expected: all tests pass.

Run: `ruff check .`

Expected: all checks pass.
