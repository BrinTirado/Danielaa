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
    router = ActionRouter(
        state=state,
        memory_store=MemoryStore(tmp_path / "memory.sqlite3"),
        navigator=FakeNavigator(house_map, state),
    )

    move = router.execute(ActionCommand(type="move", payload={"room": "kitchen"}))
    privacy = router.execute(ActionCommand(type="privacy_on", payload={}))

    assert move.succeeded is True
    assert privacy.succeeded is True
    assert state.location == "kitchen"
    assert state.privacy_mode is True


def test_router_remembers_and_forgets(tmp_path, house_map) -> None:
    state = RobotState(name="Mochi", location="living_room")
    store = MemoryStore(tmp_path / "memory.sqlite3")
    router = ActionRouter(
        state=state,
        memory_store=store,
        navigator=FakeNavigator(house_map, state),
    )

    remembered = router.execute(
        ActionCommand(
            type="remember",
            payload={"person_id": "daniela", "content": "likes quiet mode"},
        )
    )
    memory_id = remembered.payload["memory_id"]
    forgotten = router.execute(ActionCommand(type="forget", payload={"memory_id": memory_id}))

    assert remembered.succeeded is True
    assert forgotten.succeeded is True
    assert store.list_memories() == []


def test_router_invalid_action_fails(tmp_path, house_map) -> None:
    state = RobotState(name="Mochi", location="living_room")
    router = ActionRouter(
        state=state,
        memory_store=MemoryStore(tmp_path / "memory.sqlite3"),
        navigator=FakeNavigator(house_map, state),
    )
    result = router.execute(ActionCommand(type="dance", payload={}))
    assert result.succeeded is False
    assert "Unsupported action" in result.message


def test_router_speaks_payload_text(tmp_path, house_map) -> None:
    state = RobotState(name="Mochi", location="living_room")
    router = ActionRouter(
        state=state,
        memory_store=MemoryStore(tmp_path / "memory.sqlite3"),
        navigator=FakeNavigator(house_map, state),
    )

    result = router.execute(ActionCommand(type="speak", payload={"text": "hello"}))

    assert result.succeeded is True
    assert result.message == "hello"
    assert result.payload == {"text": "hello"}


def test_router_docks(tmp_path, house_map) -> None:
    state = RobotState(name="Mochi", location="living_room")
    router = ActionRouter(
        state=state,
        memory_store=MemoryStore(tmp_path / "memory.sqlite3"),
        navigator=FakeNavigator(house_map, state),
    )

    result = router.execute(ActionCommand(type="dock", payload={}))

    assert result.succeeded is True
    assert state.location == "charging_station"
    assert result.payload["destination"] == "charging_station"


def test_router_turns_privacy_off(tmp_path, house_map) -> None:
    state = RobotState(name="Mochi", location="living_room", privacy_mode=True)
    router = ActionRouter(
        state=state,
        memory_store=MemoryStore(tmp_path / "memory.sqlite3"),
        navigator=FakeNavigator(house_map, state),
    )

    result = router.execute(ActionCommand(type="privacy_off", payload={}))

    assert result.succeeded is True
    assert state.privacy_mode is False
    assert result.payload == {"privacy_mode": False}


def test_router_sets_mood(tmp_path, house_map) -> None:
    state = RobotState(name="Mochi", location="living_room")
    router = ActionRouter(
        state=state,
        memory_store=MemoryStore(tmp_path / "memory.sqlite3"),
        navigator=FakeNavigator(house_map, state),
    )

    result = router.execute(ActionCommand(type="set_mood", payload={"mood": "sleepy"}))

    assert result.succeeded is True
    assert state.mood == "sleepy"
    assert result.payload == {"mood": "sleepy"}


@pytest.mark.parametrize(
    ("command", "message"),
    [
        (ActionCommand(type="speak", payload={}), "missing text"),
        (ActionCommand(type="move", payload={"room": 123}), "room must be a string"),
        (ActionCommand(type="remember", payload={"person_id": "daniela"}), "missing content"),
        (ActionCommand(type="forget", payload={"memory_id": 123}), "memory_id must be a string"),
        (ActionCommand(type="set_mood", payload={}), "missing mood"),
    ],
)
def test_router_malformed_payload_fails(tmp_path, house_map, command, message) -> None:
    state = RobotState(name="Mochi", location="living_room")
    router = ActionRouter(
        state=state,
        memory_store=MemoryStore(tmp_path / "memory.sqlite3"),
        navigator=FakeNavigator(house_map, state),
    )

    result = router.execute(command)

    assert result.succeeded is False
    assert message in result.message


def test_router_dependency_errors_propagate(tmp_path, house_map) -> None:
    state = RobotState(name="Mochi", location="living_room")
    router = ActionRouter(
        state=state,
        memory_store=MemoryStore(tmp_path / "memory.sqlite3"),
        navigator=FakeNavigator(house_map, state=None),
    )

    with pytest.raises(TypeError, match="FakeNavigator.move_to requires a RobotState"):
        router.execute(ActionCommand(type="move", payload={"room": "kitchen"}))
