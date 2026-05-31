# Action Router Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute fake robot actions through a single router without letting conversation code touch adapters directly.

**Architecture:** `ActionRouter` receives `ActionCommand` objects and delegates to memory, navigation, or state methods. Invalid actions return structured failures instead of raising uncaught exceptions.

**Tech Stack:** Pydantic, pytest, ruff.

---

### Task 1: Action Commands and Router

**Files:**
- Modify: `src/mochi/core/models.py`
- Create: `src/mochi/actions/__init__.py`
- Create: `src/mochi/actions/action_router.py`
- Create: `src/mochi/actions/speak.py`
- Create: `src/mochi/actions/move.py`
- Create: `src/mochi/actions/privacy.py`
- Test: `tests/test_action_router.py`

- [x] **Step 1: Write tests**

```python
import pytest

from mochi.actions.action_router import ActionRouter
from mochi.core.models import ActionCommand, HouseMap, Room
from mochi.core.state import RobotState
from mochi.memory.store import MemoryStore
from mochi.navigation.fake_navigator import FakeNavigator


@pytest.fixture
def house_map() -> HouseMap:
    return HouseMap(
        default_location="living_room",
        rooms={
            "living_room": Room(connected_to=["kitchen", "charging_station"]),
            "kitchen": Room(connected_to=["living_room"]),
            "charging_station": Room(connected_to=["living_room"]),
        },
        no_go_zones=["bedroom"],
    )


def test_router_executes_move_and_privacy(tmp_path, house_map) -> None:
    state = RobotState(name="Mochi", location="living_room")
    router = ActionRouter(state=state, memory_store=MemoryStore(tmp_path / "memory.sqlite3"), navigator=FakeNavigator(house_map, state))

    move = router.execute(ActionCommand(type="move", payload={"room": "kitchen"}))
    privacy = router.execute(ActionCommand(type="privacy_on", payload={}))

    assert move.succeeded is True
    assert privacy.succeeded is True
    assert state.location == "kitchen"
    assert state.privacy_mode is True


def test_router_remembers_and_forgets(tmp_path, house_map) -> None:
    state = RobotState(name="Mochi", location="living_room")
    store = MemoryStore(tmp_path / "memory.sqlite3")
    router = ActionRouter(state=state, memory_store=store, navigator=FakeNavigator(house_map, state))

    remembered = router.execute(ActionCommand(type="remember", payload={"person_id": "daniela", "content": "likes quiet mode"}))
    memory_id = remembered.payload["memory_id"]
    forgotten = router.execute(ActionCommand(type="forget", payload={"memory_id": memory_id}))

    assert remembered.succeeded is True
    assert forgotten.succeeded is True
    assert store.list_memories() == []


def test_router_invalid_action_fails(tmp_path, house_map) -> None:
    state = RobotState(name="Mochi", location="living_room")
    router = ActionRouter(state=state, memory_store=MemoryStore(tmp_path / "memory.sqlite3"), navigator=FakeNavigator(house_map, state))
    result = router.execute(ActionCommand(type="dance", payload={}))
    assert result.succeeded is False
    assert "Unsupported action" in result.message
```

- [x] **Step 2: Run tests to verify red**

Run: `pytest tests/test_action_router.py -v`

Expected: failure for missing action modules or command model.

- [x] **Step 3: Add command/result models**

Add to `core/models.py`:

```python
ActionType = Literal["speak", "move", "dock", "remember", "forget", "privacy_on", "privacy_off", "set_mood"]


class ActionCommand(BaseModel):
    type: ActionType | str
    payload: dict[str, Any] = Field(default_factory=dict)


class ActionResult(BaseModel):
    succeeded: bool
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
```

- [x] **Step 4: Implement router behavior**

Support:
- `speak`: return message from `payload["text"]`.
- `move`: call `navigator.move_to(payload["room"])`.
- `dock`: call `navigator.dock()`.
- `remember`: call `memory_store.add_memory(person_id, content, importance)`.
- `forget`: call `memory_store.delete_memory(memory_id)`.
- `privacy_on` and `privacy_off`: update `RobotState`.
- `set_mood`: call `state.set_mood(payload["mood"])`.

- [x] **Step 5: Run verification**

Run: `pytest tests/test_action_router.py -v`

Expected: all tests pass.

Run: `pytest && ruff check .`

Expected: all tests and lint checks pass.
