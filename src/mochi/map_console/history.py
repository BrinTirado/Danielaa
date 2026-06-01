from mochi.conversation.engine import ConversationResponse
from mochi.core.models import ActionResult
from mochi.map_console.models import ConsoleTurn, MovementEvent


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

        movement_action = self._movement_action(response.actions)
        if movement_action is None:
            return

        requested_destination = self._requested_destination(movement_action)
        self.movements.append(
            MovementEvent(
                id=self._next_id,
                source=source,
                command=input_text,
                requested_destination=requested_destination,
                start_location=start_location,
                end_location=end_location,
                succeeded=movement_action.succeeded,
                message=movement_action.message,
            )
        )
        self._next_id += 1

    def _movement_action(self, actions: list[ActionResult]) -> ActionResult | None:
        for action in actions:
            if "room" in action.payload or "destination" in action.payload:
                return action
        return None

    def _requested_destination(self, action: ActionResult) -> str:
        value = action.payload.get("destination") or action.payload.get("room")
        if isinstance(value, str) and value.strip():
            return value
        return "unknown"
