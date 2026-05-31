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


def test_failed_legacy_go_to_does_not_rebind_state() -> None:
    original_state = RobotState(name="Mochi", location="living_room")
    legacy_state = RobotState(name="Mochi", location="kitchen")
    navigator = FakeNavigator(make_map(), original_state)

    result = navigator.go_to(legacy_state, "garage")

    assert result.succeeded is False
    assert navigator.state is original_state
    assert original_state.location == "living_room"
    assert legacy_state.location == "kitchen"


def test_dock_moves_to_charging_corner_when_charging_station_missing() -> None:
    house_map = HouseMap(
        default_location="living_room",
        rooms={
            "living_room": Room(connected_to=["charging_corner"]),
            "charging_corner": Room(connected_to=["living_room"]),
        },
    )
    state = RobotState(name="Mochi", location="living_room")

    result = FakeNavigator(house_map, state).dock()

    assert result.succeeded is True
    assert state.location == "charging_corner"
