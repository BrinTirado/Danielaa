from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from mochi.actions.move import dock, move
from mochi.actions.privacy import set_privacy
from mochi.actions.speak import speak
from mochi.core.models import ActionCommand, ActionResult
from mochi.core.state import RobotState
from mochi.memory.store import MemoryStore
from mochi.navigation.base import Navigator


@dataclass(frozen=True)
class ActionRouter:
    state: RobotState
    memory_store: MemoryStore
    navigator: Navigator

    def execute(self, command: ActionCommand) -> ActionResult:
        handlers: dict[str, Callable[[dict[str, Any]], ActionResult]] = {
            "speak": self._speak,
            "move": self._move,
            "dock": self._dock,
            "remember": self._remember,
            "forget": self._forget,
            "privacy_on": self._privacy_on,
            "privacy_off": self._privacy_off,
            "set_mood": self._set_mood,
        }
        handler = handlers.get(command.type)
        if handler is None:
            return self._failure(f"Unsupported action: {command.type}")

        try:
            return handler(command.payload)
        except PayloadError as exc:
            return self._failure(f"Malformed payload for {command.type}: {exc}")

    def _speak(self, payload: dict[str, Any]) -> ActionResult:
        return speak(self._required_str(payload, "text"))

    def _move(self, payload: dict[str, Any]) -> ActionResult:
        return move(self.navigator, self._required_str(payload, "room"))

    def _dock(self, payload: dict[str, Any]) -> ActionResult:
        return dock(self.navigator)

    def _remember(self, payload: dict[str, Any]) -> ActionResult:
        person_id = self._required_str(payload, "person_id")
        content = self._required_str(payload, "content")
        importance = self._optional_int(payload, "importance", default=1)
        memory = self.memory_store.add_memory(
            person_id,
            content,
            importance,
        )
        return ActionResult(
            succeeded=True,
            message="Memory saved.",
            payload={"memory_id": memory.id},
        )

    def _forget(self, payload: dict[str, Any]) -> ActionResult:
        memory_id = self._required_str(payload, "memory_id")
        deleted = self.memory_store.delete_memory(memory_id)
        if not deleted:
            return self._failure(f"Memory not found: {memory_id}")
        return ActionResult(
            succeeded=True,
            message="Memory deleted.",
            payload={"memory_id": memory_id},
        )

    def _privacy_on(self, payload: dict[str, Any]) -> ActionResult:
        return set_privacy(self.state, True)

    def _privacy_off(self, payload: dict[str, Any]) -> ActionResult:
        return set_privacy(self.state, False)

    def _set_mood(self, payload: dict[str, Any]) -> ActionResult:
        mood = self._required_str(payload, "mood")
        self.state.set_mood(mood)
        return ActionResult(
            succeeded=True,
            message=f"Mood set to {mood}.",
            payload={"mood": self.state.mood},
        )

    def _required_str(self, payload: dict[str, Any], key: str) -> str:
        if key not in payload:
            raise PayloadError(f"missing {key}")
        value = payload[key]
        if not isinstance(value, str):
            raise PayloadError(f"{key} must be a string")
        if not value.strip():
            raise PayloadError(f"{key} cannot be empty")
        return value

    def _optional_int(self, payload: dict[str, Any], key: str, *, default: int) -> int:
        if key not in payload:
            return default
        value = payload[key]
        if type(value) is not int:
            raise PayloadError(f"{key} must be an integer")
        return value

    def _failure(self, message: str) -> ActionResult:
        return ActionResult(succeeded=False, message=message)


class PayloadError(ValueError):
    pass
