from mochi.core.models import ActionResult
from mochi.navigation.base import Navigator


def move(navigator: Navigator, room: str) -> ActionResult:
    result = navigator.move_to(room)
    payload = {"room": room}
    if result.destination is not None:
        payload["destination"] = result.destination
    return ActionResult(
        succeeded=result.succeeded,
        message=result.message,
        payload=payload,
    )


def dock(navigator: Navigator) -> ActionResult:
    result = navigator.dock()
    payload = {}
    if result.destination is not None:
        payload["destination"] = result.destination
    return ActionResult(
        succeeded=result.succeeded,
        message=result.message,
        payload=payload,
    )
