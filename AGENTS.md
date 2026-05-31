# AGENTS.md

## Project

This repo builds Mochi, a software-first robot brain for a future home robot.

The current phase is software-only. Do not implement real robot hardware, ROS, cameras, microphones, or motors unless the task explicitly asks for it.

Use Python 3.11+, pytest, ruff, Typer, Rich, Pydantic, PyYAML, and local SQLite.

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
