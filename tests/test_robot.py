from mochi.navigation import FakeNavigator
from mochi.state import RobotState


def test_fake_navigation_updates_robot_location() -> None:
    state = RobotState(location="charging_corner", battery_percent=82)
    navigator = FakeNavigator(known_locations={"charging_corner", "living_room"})

    result = navigator.go_to(state, "living_room")

    assert result.succeeded is True
    assert result.message == "Mochi fake-navigated to living_room."
    assert state.location == "living_room"


def test_fake_navigation_rejects_unknown_location() -> None:
    state = RobotState(location="charging_corner", battery_percent=82)
    navigator = FakeNavigator(known_locations={"charging_corner", "living_room"})

    result = navigator.go_to(state, "garage")

    assert result.succeeded is False
    assert result.message == "Unknown location: garage."
    assert state.location == "charging_corner"
