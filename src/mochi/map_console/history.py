from dataclasses import dataclass

from mochi.conversation.engine import ConversationResponse
from mochi.core.models import ActionResult
from mochi.map_console.models import ConsoleTurn, MovementEvent


@dataclass(frozen=True)
class NavigationIntent:
    kind: str
    requested_destination: str


class MovementHistory:
    def __init__(self) -> None:
        self.last_turn: ConsoleTurn | None = None
        self.movements: list[MovementEvent] = []
        self._next_id = 1

    def record_turn(
        self,
        *,
        source: str,
        input_text: str,
        response: ConversationResponse,
        start_location: str,
        end_location: str,
    ) -> None:
        self.last_turn = ConsoleTurn(
            source=source,
            input_text=input_text,
            response_text=response.text,
            actions=response.actions,
        )

        navigation_intent = self._navigation_intent(input_text)
        if navigation_intent is None:
            return

        movement_action = self._movement_action(response.actions)
        if movement_action is None:
            return

        self.movements.append(
            MovementEvent(
                id=self._next_id,
                source=source,
                command=input_text,
                requested_destination=self._requested_destination(
                    movement_action,
                    navigation_intent,
                ),
                start_location=start_location,
                end_location=end_location,
                succeeded=movement_action.succeeded,
                message=movement_action.message,
            )
        )
        self._next_id += 1

    def _movement_action(self, actions: list[ActionResult]) -> ActionResult | None:
        return actions[0] if actions else None

    def _navigation_intent(self, input_text: str) -> NavigationIntent | None:
        command_text = input_text.strip().lower()
        if command_text == "go charge":
            return NavigationIntent(kind="dock", requested_destination="dock")
        if command_text.startswith("go to "):
            room = command_text[len("go to ") :].strip()
            if room:
                return NavigationIntent(kind="move", requested_destination=room)
        return None

    def _requested_destination(
        self,
        action: ActionResult,
        navigation_intent: NavigationIntent,
    ) -> str:
        if navigation_intent.kind == "move":
            return navigation_intent.requested_destination

        value = action.payload.get("destination") or action.payload.get("room")
        if isinstance(value, str) and value.strip():
            return value
        return navigation_intent.requested_destination
