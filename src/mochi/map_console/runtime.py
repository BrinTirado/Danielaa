from threading import RLock

from mochi.conversation.engine import ConversationEngine, ConversationResponse
from mochi.core.models import HouseMap
from mochi.core.state import RobotState
from mochi.map_console.history import MovementHistory
from mochi.map_console.models import MapSnapshot
from mochi.map_console.snapshot import build_map_snapshot
from mochi.voice.engine import VoiceEngine
from mochi.voice.fake import FakeSpeechRecognizer, FakeSpeechSynthesizer


class MapConsoleRuntime:
    def __init__(
        self,
        *,
        house_map: HouseMap,
        state: RobotState,
        conversation_engine: ConversationEngine,
        history: MovementHistory | None = None,
    ) -> None:
        self.house_map = house_map
        self.state = state
        self.conversation_engine = conversation_engine
        self.history = history or MovementHistory()
        self.last_voice_output: str | None = None
        self._lock = RLock()

    def snapshot(self) -> MapSnapshot:
        with self._lock:
            return self._snapshot_unlocked()

    def _snapshot_unlocked(self) -> MapSnapshot:
        return build_map_snapshot(
            house_map=self.house_map,
            state=self.state,
            history=self.history,
        )

    def handle_command(self, text: str, *, source: str = "map-ui") -> MapSnapshot:
        with self._lock:
            command_text = self._clean_text(text, label="Command text")
            start_location = self.state.location
            response = self.conversation_engine.respond(command_text)
            self._record(
                source=source,
                input_text=command_text,
                response=response,
                start_location=start_location,
            )
            return self._snapshot_unlocked()

    def handle_voice_text(self, text: str) -> MapSnapshot:
        with self._lock:
            voice_text = self._clean_text(text, label="Voice text")
            start_location = self.state.location
            synthesizer = FakeSpeechSynthesizer()
            voice = VoiceEngine(
                conversation_engine=self.conversation_engine,
                recognizer=FakeSpeechRecognizer([voice_text]),
                synthesizer=synthesizer,
            )
            result = voice.handle_turn()
            self.last_voice_output = result.output.text
            response = ConversationResponse(text=result.response_text, actions=result.actions)
            self._record(
                source="voice",
                input_text=result.input.text,
                response=response,
                start_location=start_location,
            )
            return self._snapshot_unlocked()

    def _record(
        self,
        *,
        source: str,
        input_text: str,
        response: ConversationResponse,
        start_location: str,
    ) -> None:
        self.history.record_turn(
            source=source,
            input_text=input_text,
            response=response,
            start_location=start_location,
            end_location=self.state.location,
        )

    def _clean_text(self, text: str, *, label: str) -> str:
        stripped = text.strip()
        if not stripped:
            msg = f"{label} cannot be empty."
            raise ValueError(msg)
        return stripped
