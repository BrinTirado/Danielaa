from mochi.core.models import ActionResult
from mochi.core.state import RobotState


def set_privacy(state: RobotState, enabled: bool) -> ActionResult:
    state.set_privacy_mode(enabled)
    status = "on" if enabled else "off"
    return ActionResult(
        succeeded=True,
        message=f"Privacy mode is {status}.",
        payload={"privacy_mode": state.privacy_mode},
    )
