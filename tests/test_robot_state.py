import pytest

from mochi.core.state import RobotState


def test_state_initializes_with_defaults() -> None:
    state = RobotState(name="Mochi", location="living_room")
    assert state.name == "Mochi"
    assert state.location == "living_room"
    assert state.battery_percent == 100
    assert state.mood == "curious"
    assert state.privacy_mode is False
    assert state.active_person is None
    assert state.last_action is None


def test_state_toggles_privacy_and_updates_location() -> None:
    state = RobotState(name="Mochi", location="living_room")
    state.set_privacy_mode(True)
    state.set_location("kitchen")
    assert state.privacy_mode is True
    assert state.location == "kitchen"
    assert state.last_action == "move:kitchen"


def test_state_rejects_invalid_battery() -> None:
    state = RobotState(name="Mochi", location="living_room")
    with pytest.raises(ValueError, match="battery"):
        state.set_battery_percent(101)
