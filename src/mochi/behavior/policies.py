from mochi.core.state import RobotState


def privacy_blocks_proactive_behavior(state: RobotState) -> bool:
    return state.privacy_mode


def needs_forced_dock(state: RobotState) -> bool:
    return state.battery_percent < 10


def should_suggest_docking(state: RobotState) -> bool:
    return state.battery_percent < 20
