# Behavior Planner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add basic autonomous behavior decisions without running a continuous loop.

**Architecture:** The planner returns suggested `ActionCommand`s. It does not execute actions directly and does not run constantly in v0.1.

**Tech Stack:** Pydantic, pytest, ruff.

---

### Task 1: Planner Policies

**Files:**
- Create: `src/mochi/behavior/__init__.py`
- Create: `src/mochi/behavior/planner.py`
- Create: `src/mochi/behavior/policies.py`
- Test: `tests/test_behavior_planner.py`

- [x] **Step 1: Write tests**

```python
from mochi.behavior.planner import BehaviorPlanner
from mochi.core.state import RobotState


def test_privacy_mode_returns_no_actions() -> None:
    state = RobotState(name="Mochi", location="living_room", privacy_mode=True, battery_percent=5)
    assert BehaviorPlanner().suggest_actions(state) == []


def test_battery_under_ten_returns_dock_action() -> None:
    state = RobotState(name="Mochi", location="living_room", battery_percent=9)
    actions = BehaviorPlanner().suggest_actions(state)
    assert actions[0].type == "dock"


def test_battery_under_twenty_suggests_docking() -> None:
    state = RobotState(name="Mochi", location="living_room", battery_percent=19)
    actions = BehaviorPlanner().suggest_actions(state)
    assert actions[0].type == "speak"
    assert "dock" in actions[0].payload["text"].lower()


def test_normal_state_returns_no_actions() -> None:
    state = RobotState(name="Mochi", location="living_room", battery_percent=80)
    assert BehaviorPlanner().suggest_actions(state) == []
```

- [x] **Step 2: Run tests to verify red**

Run: `pytest tests/test_behavior_planner.py -v`

Expected: failure for missing behavior modules.

- [x] **Step 3: Implement policy helpers**

`policies.py` should expose:

```python
def privacy_blocks_proactive_behavior(state: RobotState) -> bool
def needs_forced_dock(state: RobotState) -> bool
def should_suggest_docking(state: RobotState) -> bool
```

Use thresholds: privacy blocks all proactive actions; battery `< 10` docks; battery `< 20` suggests docking.

- [x] **Step 4: Implement planner**

`BehaviorPlanner.suggest_actions(state: RobotState) -> list[ActionCommand]` returns:
- `[]` when privacy mode is on.
- `[ActionCommand(type="dock", payload={})]` when battery is below 10.
- `[ActionCommand(type="speak", payload={"text": "My battery is low. I should go dock soon."})]` when battery is below 20.
- `[]` otherwise.

- [x] **Step 5: Run verification**

Run: `pytest tests/test_behavior_planner.py -v`

Expected: all tests pass.

Run: `pytest && ruff check .`

Expected: all tests and lint checks pass.
