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
