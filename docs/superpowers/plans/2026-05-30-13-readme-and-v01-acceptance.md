# README and v0.1 Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Mochi v0.1 usable and verify the full text-only robot brain flow.

**Architecture:** README documents the current software-only system, commands, config, privacy rules, and roadmap. Acceptance tests verify the CLI can perform the expected v0.1 user flow.

**Tech Stack:** Markdown, Typer, pytest, ruff.

---

### Task 1: README Completeness

**Files:**
- Modify: `README.md`
- Test: `tests/test_v01_acceptance.py`

- [x] **Step 1: Write acceptance tests**

```python
from typer.testing import CliRunner

from mochi.cli.main import app


runner = CliRunner()


def test_v01_chat_acceptance_flow() -> None:
    result = runner.invoke(
        app,
        ["chat"],
        input=(
            "where are you?\n"
            "go to kitchen\n"
            "remember that I like quiet mode after work\n"
            "memories\n"
            "privacy mode on\n"
            "go to bedroom\n"
            "exit\n"
        ),
    )

    assert result.exit_code == 0
    assert "living_room" in result.stdout
    assert "kitchen" in result.stdout
    assert "Noted" in result.stdout
    assert "quiet mode after work" in result.stdout
    assert "Privacy mode enabled" in result.stdout
    assert "no-go zone" in result.stdout
```

- [x] **Step 2: Run acceptance test to verify red or confirm remaining gaps**

Run: `pytest tests/test_v01_acceptance.py -v`

Expected before completion: failure showing the next missing behavior. Expected after implementation: pass.

- [x] **Step 3: Update README sections**

README must include:
- Project overview.
- Current phase: v0.1 software-only.
- Install instructions using virtualenv and `pip install -e ".[dev]"`.
- Run instructions for `mochi chat`, `mochi state`, `mochi memories`, `mochi forget`, and `mochi privacy`.
- Test instructions for `pytest` and `ruff check .`.
- Config explanation for `config/robot_profile.yaml`, `config/house_map.yaml`, and `config/people.yaml`.
- Privacy rules: explicit remember only, list/delete memories, privacy mode suppresses proactive speech.
- Future roadmap: v0.2 voice, v0.3 webcam awareness, v0.4 autonomous loop, v0.5 Home Assistant, v0.6 ROS/Gazebo, v1.0 real hardware adapter.

- [x] **Step 4: Run final v0.1 verification**

Run: `pytest`

Expected: all tests pass.

Run: `ruff check .`

Expected: all checks pass.

Run: `printf "where are you?\\ngo to kitchen\\nremember that I like quiet mode after work\\nmemories\\nprivacy mode on\\ngo to bedroom\\nexit\\n" | mochi chat`

Expected output includes:
- `living_room`
- `kitchen`
- `Noted`
- `quiet mode after work`
- `Privacy mode enabled`
- `no-go zone`

- [x] **Step 5: Summarize completion**

Report:
- Files changed.
- Commands run and results.
- Any remaining v0.1 gaps.
- Recommended next version task after v0.1.
