from mochi.core.models import ActionResult


def speak(text: str) -> ActionResult:
    return ActionResult(succeeded=True, message=text, payload={"text": text})
