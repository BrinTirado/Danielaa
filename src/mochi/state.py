from mochi.core.state import RobotState as CoreRobotState


class RobotState(CoreRobotState):
    name: str = "Mochi"
    location: str = "living_room"
    is_charging: bool = False
