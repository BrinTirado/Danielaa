# Fake Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement fake room-to-room movement that updates `RobotState` without touching real hardware.

**Architecture:** Define a navigator interface in `navigation/base.py` and a fake implementation in `navigation/fake_navigator.py`. The fake navigator validates rooms and no-go zones from `HouseMap`.

**Tech Stack:** Pydantic, pytest, ruff.

---

### Task 1: Navigator Interface and Fake Navigator

**Files:**
- Create or modify: `src/mochi/navigation/__init__.py`
- Create: `src/mochi/navigation/base.py`
- Create: `src/mochi/navigation/fake_navigator.py`
- Test: `tests/test_fake_navigation.py`

- [x] **Step 1: Write tests**

```python
from mochi.core.models import HouseMap, Room
from mochi.core.state import RobotState
from mochi.navigation.fake_navigator import FakeNavigator


def make_map() -> HouseMap:
    return HouseMap(
        default_location="living_room",
        rooms={
            "living_room": Room(connected_to=["kitchen", "hallway"]),
            "kitchen": Room(connected_to=["living_room"]),
            "charging_station": Room(connected_to=["living_room"]),
        },
        no_go_zones=["bedroom"],
    )


def test_valid_move_updates_state() -> None:
    state = RobotState(name="Mochi", location="living_room")
    result = FakeNavigator(make_map(), state).move_to("kitchen")
    assert result.succeeded is True
    assert state.location == "kitchen"


def test_no_go_zone_is_blocked() -> None:
    state = RobotState(name="Mochi", location="living_room")
    result = FakeNavigator(make_map(), state).move_to("bedroom")
    assert result.succeeded is False
    assert "no-go zone" in result.message
    assert state.location == "living_room"


def test_unknown_room_is_blocked() -> None:
    state = RobotState(name="Mochi", location="living_room")
    result = FakeNavigator(make_map(), state).move_to("attic")
    assert result.succeeded is False
    assert "Unknown room" in result.message


def test_dock_moves_to_charging_station() -> None:
    state = RobotState(name="Mochi", location="living_room")
    result = FakeNavigator(make_map(), state).dock()
    assert result.succeeded is True
    assert state.location == "charging_station"
```

- [x] **Step 2: Run tests to verify red**

Run: `pytest tests/test_fake_navigation.py -v`

Expected: failures for missing fake navigator modules or methods.

- [x] **Step 3: Implement result and interface**

`base.py` should include `NavigationResult` with `succeeded: bool`, `message: str`, and `destination: str | None`, plus a `Navigator` protocol with `move_to()` and `dock()`.

- [x] **Step 4: Implement `FakeNavigator`**

Rules:
- `move_to(room)` blocks rooms in `house_map.no_go_zones`.
- `move_to(room)` blocks rooms not present in `house_map.rooms`.
- Valid moves call `state.set_location(room)`.
- `dock()` moves to `charging_station` if it exists, otherwise `dock`, otherwise returns failure.

- [x] **Step 5: Run verification**

Run: `pytest tests/test_fake_navigation.py -v`

Expected: all tests pass.

Run: `pytest && ruff check .`

Expected: all tests and lint checks pass.
