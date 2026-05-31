from mochi.behavior.policies import (
    needs_forced_dock,
    privacy_blocks_proactive_behavior,
    should_suggest_docking,
)
from mochi.core.models import ActionCommand
from mochi.core.state import RobotState


class BehaviorPlanner:
    def suggest_actions(self, state: RobotState) -> list[ActionCommand]:
        if privacy_blocks_proactive_behavior(state):
            return []
        if needs_forced_dock(state):
            return [ActionCommand(type="dock", payload={})]
        if should_suggest_docking(state):
            return [
                ActionCommand(
                    type="speak",
                    payload={"text": "My battery is low. I should go dock soon."},
                )
            ]
        return []
