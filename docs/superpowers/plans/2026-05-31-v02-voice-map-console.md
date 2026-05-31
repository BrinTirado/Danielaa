# Mochi v0.2 Voice Map Console Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build v0.2 as fake voice input/output plus a local map console that shows Mochi's fake location, allowed paths, blocked rooms, and movement history.

**Architecture:** Keep the existing conversation system as the center. Add a `mochi.voice` package for replaceable fake voice adapters, and a `mochi.map_console` package for runtime snapshots, movement history, and a standard-library local web server. The UI talks to local JSON endpoints and never controls navigation directly; it sends text commands that flow through `ConversationEngine` and `ActionRouter`.

**Tech Stack:** Python 3.11+, Typer, Rich, Pydantic, PyYAML, local SQLite, standard-library `http.server`, pytest, ruff, vanilla HTML/CSS/JavaScript.

---

## File Structure

- Modify `src/mochi/core/models.py`: add optional room map coordinates.
- Modify `config/house_map.yaml`: add stable room positions for the current fake map.
- Create `src/mochi/voice/__init__.py`: export voice models and fake adapters.
- Create `src/mochi/voice/base.py`: define speech recognizer and synthesizer protocols.
- Create `src/mochi/voice/models.py`: define `SpeechInput`, `SpeechOutput`, and `VoiceTurnResult`.
- Create `src/mochi/voice/fake.py`: implement `FakeSpeechRecognizer` and `FakeSpeechSynthesizer`.
- Create `src/mochi/voice/engine.py`: coordinate one fake voice turn through `ConversationEngine`.
- Create `src/mochi/map_console/__init__.py`: export console runtime and server helpers.
- Create `src/mochi/map_console/models.py`: define map snapshot, console turn, and movement event models.
- Create `src/mochi/map_console/history.py`: track last turn and movement events in memory.
- Create `src/mochi/map_console/snapshot.py`: convert `HouseMap`, `RobotState`, and history into JSON-ready snapshots.
- Create `src/mochi/map_console/runtime.py`: coordinate command turns and voice turns for the UI.
- Create `src/mochi/map_console/static.py`: hold the local console HTML.
- Create `src/mochi/map_console/server.py`: serve the UI and JSON endpoints using the standard library.
- Modify `src/mochi/cli/main.py`: include `house_map` in runtime, add `voice` and `map-ui` commands.
- Modify `README.md`: document v0.2 commands and boundaries.
- Create tests:
  - `tests/test_voice.py`
  - `tests/test_map_console.py`
  - `tests/test_map_console_server.py`
  - update `tests/test_config_loading.py`
  - update `tests/test_cli.py`
  - add or update v0.2 acceptance tests in `tests/test_v02_acceptance.py`

---

### Task 1: Add Room Map Positions

**Files:**
- Modify: `src/mochi/core/models.py`
- Modify: `config/house_map.yaml`
- Modify: `tests/test_config_loading.py`

- [ ] **Step 1: Write the failing config test**

Add this assertion to `test_load_house_map` in `tests/test_config_loading.py`:

```python
def test_load_house_map() -> None:
    house_map = load_house_map(CONFIG_DIR / "house_map.yaml")
    assert house_map.default_location == "living_room"
    assert "kitchen" in house_map.rooms
    assert "bedroom" in house_map.no_go_zones
    assert house_map.rooms["living_room"].map_position is not None
    assert house_map.rooms["living_room"].map_position.x == 160
    assert house_map.rooms["living_room"].map_position.y == 160
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
pytest tests/test_config_loading.py::test_load_house_map -v
```

Expected: fail with an attribute or validation error because `Room.map_position` does not exist yet.

- [ ] **Step 3: Implement map position models**

Update `src/mochi/core/models.py` so the room models include optional coordinates:

```python
class MapPosition(MochiBaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)


class Room(MochiBaseModel):
    display_name: str = ""
    description: str = ""
    connected_to: list[str] = Field(default_factory=list)
    map_position: MapPosition | None = None
```

Keep `MochiBaseModel`, `PersonalityConfig`, and the other existing classes unchanged.

- [ ] **Step 4: Add stable positions to the fake map config**

Update `config/house_map.yaml`:

```yaml
default_location: living_room
rooms:
  living_room:
    display_name: Living Room
    description: Main shared room for conversation and lounging.
    connected_to:
      - kitchen
      - charging_corner
    map_position:
      x: 160
      y: 160
  kitchen:
    display_name: Kitchen
    description: Food prep and household task area.
    connected_to:
      - living_room
    map_position:
      x: 420
      y: 90
  charging_corner:
    display_name: Charging Corner
    description: Mochi's fake dock location for v0.1.
    connected_to:
      - living_room
    map_position:
      x: 420
      y: 250
no_go_zones:
  - bedroom
```

- [ ] **Step 5: Run the focused config tests**

Run:

```bash
pytest tests/test_config_loading.py -v
```

Expected: all tests in `tests/test_config_loading.py` pass.

- [ ] **Step 6: Commit**

```bash
git add src/mochi/core/models.py config/house_map.yaml tests/test_config_loading.py
git commit -m "Add fake map room positions"
```

---

### Task 2: Add Fake Voice Interfaces And Engine

**Files:**
- Create: `src/mochi/voice/__init__.py`
- Create: `src/mochi/voice/base.py`
- Create: `src/mochi/voice/models.py`
- Create: `src/mochi/voice/fake.py`
- Create: `src/mochi/voice/engine.py`
- Create: `tests/test_voice.py`

- [ ] **Step 1: Write failing voice tests**

Create `tests/test_voice.py`:

```python
from collections.abc import Callable

import pytest

from mochi.actions.action_router import ActionRouter
from mochi.conversation.engine import ConversationEngine
from mochi.conversation.fake_llm import FakeLLM
from mochi.core.models import (
    HouseMap,
    PeopleConfig,
    PersonalityConfig,
    PersonProfile,
    RobotProfile,
    Room,
)
from mochi.core.state import RobotState
from mochi.memory.store import MemoryStore
from mochi.navigation.fake_navigator import FakeNavigator
from mochi.personality.prompt_builder import PersonalityPromptBuilder
from mochi.voice.engine import VoiceEngine
from mochi.voice.fake import FakeSpeechRecognizer, FakeSpeechSynthesizer


@pytest.fixture
def engine_factory(tmp_path) -> Callable[..., ConversationEngine]:
    def build_engine() -> ConversationEngine:
        profile = RobotProfile(
            name="Mochi",
            personality=PersonalityConfig(
                vibe="playful",
                energy_level="medium",
                humor_style="dry",
                talkativeness="low",
            ),
            rules=["Do not pretend to have real hardware in v0.1."],
            catchphrases=["Tiny robot brain engaged."],
        )
        people = PeopleConfig(
            people={
                "daniela": PersonProfile(
                    display_name="Daniela",
                    relationship="owner/friend",
                    greeting_style="warm",
                )
            }
        )
        house_map = HouseMap(
            default_location="living_room",
            rooms={
                "living_room": Room(connected_to=["kitchen", "charging_corner"]),
                "kitchen": Room(connected_to=["living_room"]),
                "charging_corner": Room(connected_to=["living_room"]),
            },
            no_go_zones=["bedroom"],
        )
        state = RobotState(name="Mochi", location="living_room")
        store = MemoryStore(tmp_path / "memory.sqlite3")
        navigator = FakeNavigator(house_map, state)
        router = ActionRouter(state=state, memory_store=store, navigator=navigator)
        return ConversationEngine(
            state=state,
            memory_store=store,
            action_router=router,
            prompt_builder=PersonalityPromptBuilder(profile),
            llm=FakeLLM(response="Tiny robot brain engaged."),
            people=people,
        )

    return build_engine


def test_fake_recognizer_returns_queued_text() -> None:
    recognizer = FakeSpeechRecognizer(["go to kitchen"])

    speech = recognizer.listen()

    assert speech.text == "go to kitchen"
    assert speech.source == "fake"
    assert speech.confidence == 1.0


def test_fake_recognizer_rejects_empty_queue() -> None:
    recognizer = FakeSpeechRecognizer([])

    with pytest.raises(ValueError, match="No fake speech input queued"):
        recognizer.listen()


def test_fake_synthesizer_records_spoken_text() -> None:
    synthesizer = FakeSpeechSynthesizer()

    output = synthesizer.speak("I am in living_room.")

    assert output.text == "I am in living_room."
    assert synthesizer.spoken_texts == ["I am in living_room."]


def test_voice_engine_routes_speech_to_conversation(engine_factory) -> None:
    engine = engine_factory()
    recognizer = FakeSpeechRecognizer(["where are you?"])
    synthesizer = FakeSpeechSynthesizer()
    voice = VoiceEngine(
        conversation_engine=engine,
        recognizer=recognizer,
        synthesizer=synthesizer,
    )

    result = voice.handle_turn(person_id="daniela")

    assert result.input.text == "where are you?"
    assert "living_room" in result.response_text
    assert result.output.text == result.response_text
    assert synthesizer.spoken_texts == [result.response_text]


def test_voice_engine_can_move_fake_robot(engine_factory) -> None:
    engine = engine_factory()
    voice = VoiceEngine(
        conversation_engine=engine,
        recognizer=FakeSpeechRecognizer(["go to kitchen"]),
        synthesizer=FakeSpeechSynthesizer(),
    )

    result = voice.handle_turn(person_id="daniela")

    assert engine.state.location == "kitchen"
    assert result.actions[0].succeeded is True
    assert result.output.text == result.response_text


def test_voice_turn_does_not_auto_save_memory(engine_factory) -> None:
    engine = engine_factory()
    voice = VoiceEngine(
        conversation_engine=engine,
        recognizer=FakeSpeechRecognizer(["I like quiet mode after work"]),
        synthesizer=FakeSpeechSynthesizer(),
    )

    voice.handle_turn(person_id="daniela")

    assert engine.memory_store.list_memories() == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/test_voice.py -v
```

Expected: import failure for `mochi.voice`.

- [ ] **Step 3: Add voice models**

Create `src/mochi/voice/models.py`:

```python
from pydantic import Field

from mochi.core.models import ActionResult, MochiBaseModel


class SpeechInput(MochiBaseModel):
    text: str
    source: str = "fake"
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class SpeechOutput(MochiBaseModel):
    text: str
    voice_id: str = "fake"
    audio_path: str | None = None


class VoiceTurnResult(MochiBaseModel):
    input: SpeechInput
    response_text: str
    output: SpeechOutput
    actions: list[ActionResult] = Field(default_factory=list)
```

- [ ] **Step 4: Add voice protocols**

Create `src/mochi/voice/base.py`:

```python
from typing import Protocol

from mochi.voice.models import SpeechInput, SpeechOutput


class SpeechRecognizer(Protocol):
    def listen(self) -> SpeechInput:
        """Return one recognized speech input."""
        ...


class SpeechSynthesizer(Protocol):
    def speak(self, text: str) -> SpeechOutput:
        """Return one synthesized speech output."""
        ...
```

- [ ] **Step 5: Add fake voice adapters**

Create `src/mochi/voice/fake.py`:

```python
from collections.abc import Iterable

from mochi.voice.models import SpeechInput, SpeechOutput


class FakeSpeechRecognizer:
    def __init__(self, queued_text: Iterable[str]) -> None:
        self._queued_text = list(queued_text)

    def listen(self) -> SpeechInput:
        if not self._queued_text:
            msg = "No fake speech input queued."
            raise ValueError(msg)
        text = self._queued_text.pop(0).strip()
        if not text:
            msg = "Fake speech input cannot be empty."
            raise ValueError(msg)
        return SpeechInput(text=text, source="fake", confidence=1.0)


class FakeSpeechSynthesizer:
    def __init__(self) -> None:
        self.spoken_texts: list[str] = []

    def speak(self, text: str) -> SpeechOutput:
        stripped_text = text.strip()
        if not stripped_text:
            msg = "Speech output cannot be empty."
            raise ValueError(msg)
        self.spoken_texts.append(stripped_text)
        return SpeechOutput(text=stripped_text, voice_id="fake")
```

- [ ] **Step 6: Add the voice engine**

Create `src/mochi/voice/engine.py`:

```python
from mochi.conversation.engine import ConversationEngine
from mochi.voice.base import SpeechRecognizer, SpeechSynthesizer
from mochi.voice.models import VoiceTurnResult


class VoiceEngine:
    def __init__(
        self,
        *,
        conversation_engine: ConversationEngine,
        recognizer: SpeechRecognizer,
        synthesizer: SpeechSynthesizer,
    ) -> None:
        self.conversation_engine = conversation_engine
        self.recognizer = recognizer
        self.synthesizer = synthesizer

    def handle_turn(self, person_id: str | None = None) -> VoiceTurnResult:
        speech_input = self.recognizer.listen()
        response = self.conversation_engine.respond(speech_input.text, person_id=person_id)
        speech_output = self.synthesizer.speak(response.text)
        return VoiceTurnResult(
            input=speech_input,
            response_text=response.text,
            output=speech_output,
            actions=response.actions,
        )
```

- [ ] **Step 7: Export the voice package**

Create `src/mochi/voice/__init__.py`:

```python
from mochi.voice.engine import VoiceEngine
from mochi.voice.fake import FakeSpeechRecognizer, FakeSpeechSynthesizer
from mochi.voice.models import SpeechInput, SpeechOutput, VoiceTurnResult

__all__ = [
    "FakeSpeechRecognizer",
    "FakeSpeechSynthesizer",
    "SpeechInput",
    "SpeechOutput",
    "VoiceEngine",
    "VoiceTurnResult",
]
```

- [ ] **Step 8: Run the focused voice tests**

Run:

```bash
pytest tests/test_voice.py -v
```

Expected: all tests in `tests/test_voice.py` pass.

- [ ] **Step 9: Commit**

```bash
git add src/mochi/voice tests/test_voice.py
git commit -m "Add fake voice turn engine"
```

---

### Task 3: Add Movement History And Map Snapshots

**Files:**
- Create: `src/mochi/map_console/__init__.py`
- Create: `src/mochi/map_console/models.py`
- Create: `src/mochi/map_console/history.py`
- Create: `src/mochi/map_console/snapshot.py`
- Create: `tests/test_map_console.py`

- [ ] **Step 1: Write failing map console tests**

Create `tests/test_map_console.py`:

```python
from mochi.conversation.engine import ConversationResponse
from mochi.core.models import ActionResult, HouseMap, Room
from mochi.core.state import RobotState
from mochi.map_console.history import MovementHistory
from mochi.map_console.snapshot import build_map_snapshot


def make_map() -> HouseMap:
    return HouseMap(
        default_location="living_room",
        rooms={
            "living_room": Room(
                display_name="Living Room",
                connected_to=["kitchen", "charging_corner"],
            ),
            "kitchen": Room(display_name="Kitchen", connected_to=["living_room"]),
            "charging_corner": Room(
                display_name="Charging Corner",
                connected_to=["living_room"],
            ),
        },
        no_go_zones=["bedroom"],
    )


def test_history_records_successful_move() -> None:
    history = MovementHistory()
    response = ConversationResponse(
        text="Mochi fake-navigated to kitchen.",
        actions=[
            ActionResult(
                succeeded=True,
                message="Mochi fake-navigated to kitchen.",
                payload={"room": "kitchen", "destination": "kitchen"},
            )
        ],
    )

    history.record_turn(
        source="map-ui",
        input_text="go to kitchen",
        response=response,
        start_location="living_room",
        end_location="kitchen",
    )

    assert history.last_turn is not None
    assert history.last_turn.input_text == "go to kitchen"
    assert history.movements[0].requested_destination == "kitchen"
    assert history.movements[0].start_location == "living_room"
    assert history.movements[0].end_location == "kitchen"
    assert history.movements[0].succeeded is True


def test_history_records_blocked_move_without_location_change() -> None:
    history = MovementHistory()
    response = ConversationResponse(
        text="bedroom is a no-go zone.",
        actions=[
            ActionResult(
                succeeded=False,
                message="bedroom is a no-go zone.",
                payload={"room": "bedroom", "destination": "bedroom"},
            )
        ],
    )

    history.record_turn(
        source="map-ui",
        input_text="go to bedroom",
        response=response,
        start_location="living_room",
        end_location="living_room",
    )

    event = history.movements[0]
    assert event.requested_destination == "bedroom"
    assert event.end_location == "living_room"
    assert event.succeeded is False
    assert "no-go zone" in event.message


def test_non_movement_turn_updates_last_turn_only() -> None:
    history = MovementHistory()
    response = ConversationResponse(text="I am in living_room.")

    history.record_turn(
        source="map-ui",
        input_text="where are you?",
        response=response,
        start_location="living_room",
        end_location="living_room",
    )

    assert history.last_turn is not None
    assert history.last_turn.response_text == "I am in living_room."
    assert history.movements == []


def test_build_map_snapshot_contains_rooms_state_and_history() -> None:
    history = MovementHistory()
    response = ConversationResponse(
        text="Mochi fake-navigated to kitchen.",
        actions=[
            ActionResult(
                succeeded=True,
                message="Mochi fake-navigated to kitchen.",
                payload={"room": "kitchen", "destination": "kitchen"},
            )
        ],
    )
    history.record_turn(
        source="voice",
        input_text="go to kitchen",
        response=response,
        start_location="living_room",
        end_location="kitchen",
    )
    snapshot = build_map_snapshot(
        house_map=make_map(),
        state=RobotState(name="Mochi", location="kitchen", battery_percent=86),
        history=history,
    )

    assert snapshot.current_location == "kitchen"
    assert snapshot.battery_percent == 86
    assert snapshot.rooms[0].id == "living_room"
    assert snapshot.rooms[0].connected_to == ["kitchen", "charging_corner"]
    assert snapshot.no_go_zones == ["bedroom"]
    assert snapshot.movements[0].source == "voice"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/test_map_console.py -v
```

Expected: import failure for `mochi.map_console`.

- [ ] **Step 3: Add map console models**

Create `src/mochi/map_console/models.py`:

```python
from pydantic import Field

from mochi.core.models import ActionResult, MochiBaseModel


class ConsoleTurn(MochiBaseModel):
    source: str
    input_text: str
    response_text: str
    actions: list[ActionResult] = Field(default_factory=list)


class MovementEvent(MochiBaseModel):
    id: int
    source: str
    command: str
    requested_destination: str
    start_location: str
    end_location: str
    succeeded: bool
    message: str


class RoomSnapshot(MochiBaseModel):
    id: str
    display_name: str
    description: str
    connected_to: list[str] = Field(default_factory=list)
    no_go_zone: bool = False
    x: int
    y: int


class MapSnapshot(MochiBaseModel):
    robot_name: str
    current_location: str
    battery_percent: int
    mood: str
    privacy_mode: bool
    rooms: list[RoomSnapshot] = Field(default_factory=list)
    no_go_zones: list[str] = Field(default_factory=list)
    last_turn: ConsoleTurn | None = None
    movements: list[MovementEvent] = Field(default_factory=list)
```

- [ ] **Step 4: Add movement history**

Create `src/mochi/map_console/history.py`:

```python
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
```

- [ ] **Step 5: Add snapshot builder**

Create `src/mochi/map_console/snapshot.py`:

```python
from mochi.core.models import HouseMap, Room
from mochi.core.state import RobotState
from mochi.map_console.history import MovementHistory
from mochi.map_console.models import MapSnapshot, RoomSnapshot


def build_map_snapshot(
    *,
    house_map: HouseMap,
    state: RobotState,
    history: MovementHistory,
) -> MapSnapshot:
    return MapSnapshot(
        robot_name=state.name,
        current_location=state.location,
        battery_percent=state.battery_percent,
        mood=state.mood,
        privacy_mode=state.privacy_mode,
        rooms=[
            _room_snapshot(room_id, room, index, house_map.no_go_zones)
            for index, (room_id, room) in enumerate(house_map.rooms.items())
        ],
        no_go_zones=house_map.no_go_zones,
        last_turn=history.last_turn,
        movements=history.movements,
    )


def _room_snapshot(
    room_id: str,
    room: Room,
    index: int,
    no_go_zones: list[str],
) -> RoomSnapshot:
    x, y = _room_position(room, index)
    return RoomSnapshot(
        id=room_id,
        display_name=room.display_name or room_id,
        description=room.description,
        connected_to=room.connected_to,
        no_go_zone=room_id in no_go_zones,
        x=x,
        y=y,
    )


def _room_position(room: Room, index: int) -> tuple[int, int]:
    if room.map_position is not None:
        return room.map_position.x, room.map_position.y
    return 140 + (index % 3) * 220, 120 + (index // 3) * 160
```

- [ ] **Step 6: Export map console helpers**

Create `src/mochi/map_console/__init__.py`:

```python
from mochi.map_console.history import MovementHistory
from mochi.map_console.models import ConsoleTurn, MapSnapshot, MovementEvent, RoomSnapshot
from mochi.map_console.snapshot import build_map_snapshot

__all__ = [
    "ConsoleTurn",
    "MapSnapshot",
    "MovementEvent",
    "MovementHistory",
    "RoomSnapshot",
    "build_map_snapshot",
]
```

- [ ] **Step 7: Run focused map console tests**

Run:

```bash
pytest tests/test_map_console.py -v
```

Expected: all tests in `tests/test_map_console.py` pass.

- [ ] **Step 8: Commit**

```bash
git add src/mochi/map_console tests/test_map_console.py
git commit -m "Add fake map console snapshots"
```

---

### Task 4: Add Map Console Runtime

**Files:**
- Create: `src/mochi/map_console/runtime.py`
- Modify: `src/mochi/map_console/__init__.py`
- Modify: `tests/test_map_console.py`

- [ ] **Step 1: Add failing runtime tests**

Append these tests to `tests/test_map_console.py`:

```python
from mochi.actions.action_router import ActionRouter
from mochi.conversation.engine import ConversationEngine
from mochi.conversation.fake_llm import FakeLLM
from mochi.core.models import PeopleConfig, PersonalityConfig, RobotProfile
from mochi.map_console.runtime import MapConsoleRuntime
from mochi.memory.store import MemoryStore
from mochi.navigation.fake_navigator import FakeNavigator
from mochi.personality.prompt_builder import PersonalityPromptBuilder


def make_runtime(tmp_path) -> MapConsoleRuntime:
    house_map = make_map()
    profile = RobotProfile(
        name="Mochi",
        personality=PersonalityConfig(
            vibe="playful",
            energy_level="medium",
            humor_style="dry",
            talkativeness="low",
        ),
        rules=[],
        catchphrases=[],
    )
    state = RobotState(name="Mochi", location="living_room")
    store = MemoryStore(tmp_path / "memory.sqlite3")
    router = ActionRouter(
        state=state,
        memory_store=store,
        navigator=FakeNavigator(house_map, state),
    )
    conversation = ConversationEngine(
        state=state,
        memory_store=store,
        action_router=router,
        prompt_builder=PersonalityPromptBuilder(profile),
        llm=FakeLLM(response="Tiny robot brain engaged."),
        people=PeopleConfig(),
    )
    return MapConsoleRuntime(
        house_map=house_map,
        state=state,
        conversation_engine=conversation,
    )


def test_runtime_command_updates_snapshot_and_history(tmp_path) -> None:
    runtime = make_runtime(tmp_path)

    snapshot = runtime.handle_command("go to kitchen")

    assert snapshot.current_location == "kitchen"
    assert snapshot.last_turn is not None
    assert snapshot.last_turn.input_text == "go to kitchen"
    assert snapshot.movements[0].requested_destination == "kitchen"


def test_runtime_voice_turn_records_voice_source(tmp_path) -> None:
    runtime = make_runtime(tmp_path)

    snapshot = runtime.handle_voice_text("go to kitchen")

    assert snapshot.current_location == "kitchen"
    assert snapshot.last_turn is not None
    assert snapshot.last_turn.source == "voice"
    assert snapshot.movements[0].source == "voice"


def test_runtime_empty_command_raises_value_error(tmp_path) -> None:
    runtime = make_runtime(tmp_path)

    with pytest.raises(ValueError, match="Command text cannot be empty"):
        runtime.handle_command(" ")
```

- [ ] **Step 2: Run runtime tests to verify they fail**

Run:

```bash
pytest tests/test_map_console.py -v
```

Expected: import failure for `MapConsoleRuntime`.

- [ ] **Step 3: Implement the runtime**

Create `src/mochi/map_console/runtime.py`:

```python
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

    def snapshot(self) -> MapSnapshot:
        return build_map_snapshot(
            house_map=self.house_map,
            state=self.state,
            history=self.history,
        )

    def handle_command(self, text: str, *, source: str = "map-ui") -> MapSnapshot:
        command_text = self._clean_text(text, label="Command text")
        start_location = self.state.location
        response = self.conversation_engine.respond(command_text)
        self._record(
            source=source,
            input_text=command_text,
            response=response,
            start_location=start_location,
        )
        return self.snapshot()

    def handle_voice_text(self, text: str) -> MapSnapshot:
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
        return self.snapshot()

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
```

- [ ] **Step 4: Export the runtime**

Update `src/mochi/map_console/__init__.py`:

```python
from mochi.map_console.history import MovementHistory
from mochi.map_console.models import ConsoleTurn, MapSnapshot, MovementEvent, RoomSnapshot
from mochi.map_console.runtime import MapConsoleRuntime
from mochi.map_console.snapshot import build_map_snapshot

__all__ = [
    "ConsoleTurn",
    "MapConsoleRuntime",
    "MapSnapshot",
    "MovementEvent",
    "MovementHistory",
    "RoomSnapshot",
    "build_map_snapshot",
]
```

- [ ] **Step 5: Run focused runtime tests**

Run:

```bash
pytest tests/test_map_console.py -v
```

Expected: all tests in `tests/test_map_console.py` pass.

- [ ] **Step 6: Commit**

```bash
git add src/mochi/map_console tests/test_map_console.py
git commit -m "Add map console runtime"
```

---

### Task 5: Add Local Map Console Server And UI

**Files:**
- Create: `src/mochi/map_console/static.py`
- Create: `src/mochi/map_console/server.py`
- Modify: `src/mochi/map_console/__init__.py`
- Create: `tests/test_map_console_server.py`

- [ ] **Step 1: Write failing server tests**

Create `tests/test_map_console_server.py`:

```python
import json
import threading
from http.client import HTTPConnection

import pytest

from mochi.actions.action_router import ActionRouter
from mochi.conversation.engine import ConversationEngine
from mochi.conversation.fake_llm import FakeLLM
from mochi.core.models import HouseMap, PeopleConfig, PersonalityConfig, RobotProfile, Room
from mochi.core.state import RobotState
from mochi.map_console.runtime import MapConsoleRuntime
from mochi.map_console.server import create_server
from mochi.memory.store import MemoryStore
from mochi.navigation.fake_navigator import FakeNavigator
from mochi.personality.prompt_builder import PersonalityPromptBuilder


@pytest.fixture
def console_runtime(tmp_path) -> MapConsoleRuntime:
    house_map = HouseMap(
        default_location="living_room",
        rooms={
            "living_room": Room(connected_to=["kitchen"]),
            "kitchen": Room(connected_to=["living_room"]),
        },
        no_go_zones=["bedroom"],
    )
    profile = RobotProfile(
        name="Mochi",
        personality=PersonalityConfig(
            vibe="playful",
            energy_level="medium",
            humor_style="dry",
            talkativeness="low",
        ),
    )
    state = RobotState(name="Mochi", location="living_room")
    store = MemoryStore(tmp_path / "memory.sqlite3")
    router = ActionRouter(
        state=state,
        memory_store=store,
        navigator=FakeNavigator(house_map, state),
    )
    conversation = ConversationEngine(
        state=state,
        memory_store=store,
        action_router=router,
        prompt_builder=PersonalityPromptBuilder(profile),
        llm=FakeLLM(response="Tiny robot brain engaged."),
        people=PeopleConfig(),
    )
    return MapConsoleRuntime(
        house_map=house_map,
        state=state,
        conversation_engine=conversation,
    )


def request_json(port: int, method: str, path: str, payload: dict | None = None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    connection = HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        raw = response.read().decode("utf-8")
        return response.status, json.loads(raw)
    finally:
        connection.close()


def test_server_serves_console_html(console_runtime) -> None:
    server = create_server(console_runtime, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        connection.request("GET", "/")
        response = connection.getresponse()
        html = response.read().decode("utf-8")
    finally:
        connection.close()
        server.shutdown()
        server.server_close()

    assert response.status == 200
    assert "Mochi Map Console" in html


def test_snapshot_endpoint_returns_current_location(console_runtime) -> None:
    server = create_server(console_runtime, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, body = request_json(server.server_port, "GET", "/api/snapshot")
    finally:
        server.shutdown()
        server.server_close()

    assert status == 200
    assert body["current_location"] == "living_room"


def test_command_endpoint_moves_robot(console_runtime) -> None:
    server = create_server(console_runtime, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, body = request_json(
            server.server_port,
            "POST",
            "/api/command",
            {"text": "go to kitchen"},
        )
    finally:
        server.shutdown()
        server.server_close()

    assert status == 200
    assert body["current_location"] == "kitchen"
    assert body["movements"][0]["requested_destination"] == "kitchen"


def test_voice_turn_endpoint_blocks_empty_input(console_runtime) -> None:
    server = create_server(console_runtime, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, body = request_json(
            server.server_port,
            "POST",
            "/api/voice-turn",
            {"text": " "},
        )
    finally:
        server.shutdown()
        server.server_close()

    assert status == 400
    assert "cannot be empty" in body["error"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/test_map_console_server.py -v
```

Expected: import failure for `mochi.map_console.server`.

- [ ] **Step 3: Add the static UI**

Create `src/mochi/map_console/static.py` with this complete local app shell:

```python
APP_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mochi Map Console</title>
  <style>
    body {
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f6f7f9;
      color: #172033;
    }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px 20px;
      border-bottom: 1px solid #d8dee8;
      background: #ffffff;
    }
    h1 {
      margin: 0;
      font-size: 20px;
      font-weight: 700;
    }
    main {
      display: grid;
      grid-template-columns: minmax(0, 1.5fr) 380px;
      gap: 16px;
      padding: 16px;
    }
    section {
      background: #ffffff;
      border: 1px solid #d8dee8;
      border-radius: 8px;
      padding: 14px;
    }
    h2 {
      margin: 0 0 12px;
      font-size: 15px;
    }
    #map {
      width: 100%;
      min-height: 480px;
      background: #eef2f7;
      border-radius: 8px;
      border: 1px solid #ccd6e3;
    }
    .stack {
      display: grid;
      gap: 16px;
    }
    .row {
      display: flex;
      gap: 8px;
    }
    input {
      flex: 1;
      min-width: 0;
      padding: 10px;
      border: 1px solid #b8c2d1;
      border-radius: 6px;
      font: inherit;
    }
    button {
      padding: 10px 12px;
      border: 0;
      border-radius: 6px;
      background: #2563eb;
      color: white;
      font: inherit;
      font-weight: 650;
      cursor: pointer;
    }
    button.secondary {
      background: #0f766e;
    }
    dl {
      display: grid;
      grid-template-columns: 120px 1fr;
      gap: 8px;
      margin: 0;
      font-size: 14px;
    }
    dt {
      color: #667085;
    }
    dd {
      margin: 0;
      font-weight: 650;
    }
    ul {
      margin: 0;
      padding-left: 18px;
      font-size: 14px;
    }
    li {
      margin-bottom: 8px;
    }
    .error {
      color: #b42318;
      font-weight: 650;
    }
    @media (max-width: 920px) {
      main {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <header>
    <h1>Mochi Map Console</h1>
    <div id="status">Loading...</div>
  </header>
  <main>
    <section>
      <h2>House Map</h2>
      <svg id="map" viewBox="0 0 700 520" role="img" aria-label="Mochi house map"></svg>
    </section>
    <div class="stack">
      <section>
        <h2>Fake Command</h2>
        <div class="row">
          <input id="command" value="go to kitchen" aria-label="Command text">
          <button onclick="sendCommand()">Run</button>
        </div>
      </section>
      <section>
        <h2>Fake Voice Turn</h2>
        <div class="row">
          <input id="voice" value="where are you?" aria-label="Voice text">
          <button class="secondary" onclick="sendVoice()">Speak</button>
        </div>
      </section>
      <section>
        <h2>State</h2>
        <dl id="state"></dl>
      </section>
      <section>
        <h2>Last Turn</h2>
        <div id="last-turn">No turns yet.</div>
      </section>
      <section>
        <h2>Movement History</h2>
        <ul id="history"></ul>
      </section>
    </div>
  </main>
  <script>
    async function loadSnapshot() {
      const response = await fetch("/api/snapshot");
      render(await response.json());
    }

    async function postJson(path, payload) {
      const response = await fetch(path, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
      });
      const body = await response.json();
      if (!response.ok) {
        document.getElementById("status").innerHTML = '<span class="error">' + body.error + '</span>';
        return;
      }
      render(body);
    }

    function sendCommand() {
      postJson("/api/command", {text: document.getElementById("command").value});
    }

    function sendVoice() {
      postJson("/api/voice-turn", {text: document.getElementById("voice").value});
    }

    function render(snapshot) {
      document.getElementById("status").textContent = "Location: " + snapshot.current_location;
      renderState(snapshot);
      renderLastTurn(snapshot);
      renderHistory(snapshot);
      renderMap(snapshot);
    }

    function renderState(snapshot) {
      document.getElementById("state").innerHTML = [
        ["Name", snapshot.robot_name],
        ["Location", snapshot.current_location],
        ["Battery", snapshot.battery_percent + "%"],
        ["Mood", snapshot.mood],
        ["Privacy", snapshot.privacy_mode ? "on" : "off"]
      ].map(([key, value]) => "<dt>" + key + "</dt><dd>" + value + "</dd>").join("");
    }

    function renderLastTurn(snapshot) {
      const node = document.getElementById("last-turn");
      if (!snapshot.last_turn) {
        node.textContent = "No turns yet.";
        return;
      }
      node.textContent = snapshot.last_turn.source + ": " + snapshot.last_turn.input_text + " -> " + snapshot.last_turn.response_text;
    }

    function renderHistory(snapshot) {
      const history = document.getElementById("history");
      if (!snapshot.movements.length) {
        history.innerHTML = "<li>No movement yet.</li>";
        return;
      }
      history.innerHTML = snapshot.movements.map((event) => {
        const status = event.succeeded ? "succeeded" : "blocked";
        return "<li>#" + event.id + " " + event.command + " " + status + ": " + event.start_location + " -> " + event.end_location + "</li>";
      }).join("");
    }

    function renderMap(snapshot) {
      const svg = document.getElementById("map");
      const rooms = Object.fromEntries(snapshot.rooms.map((room) => [room.id, room]));
      const lines = [];
      snapshot.rooms.forEach((room) => {
        room.connected_to.forEach((targetId) => {
          const target = rooms[targetId];
          if (!target || room.id > targetId) {
            return;
          }
          lines.push('<line x1="' + room.x + '" y1="' + room.y + '" x2="' + target.x + '" y2="' + target.y + '" stroke="#94a3b8" stroke-width="8" stroke-linecap="round"></line>');
        });
      });
      const roomNodes = snapshot.rooms.map((room) => {
        const current = room.id === snapshot.current_location;
        const fill = current ? "#dbeafe" : "#ffffff";
        const stroke = current ? "#2563eb" : "#64748b";
        return '<g><circle cx="' + room.x + '" cy="' + room.y + '" r="54" fill="' + fill + '" stroke="' + stroke + '" stroke-width="4"></circle><text x="' + room.x + '" y="' + (room.y - 4) + '" text-anchor="middle" font-size="16" font-weight="700" fill="#172033">' + room.display_name + '</text><text x="' + room.x + '" y="' + (room.y + 20) + '" text-anchor="middle" font-size="13" fill="#475467">' + (current ? "Mochi here" : room.id) + '</text></g>';
      });
      const blocked = snapshot.no_go_zones.map((roomId, index) => {
        const x = 120 + index * 180;
        const y = 450;
        return '<g><rect x="' + (x - 70) + '" y="' + (y - 30) + '" width="140" height="60" rx="8" fill="#fee2e2" stroke="#dc2626" stroke-width="3"></rect><text x="' + x + '" y="' + (y + 5) + '" text-anchor="middle" font-size="15" font-weight="700" fill="#991b1b">' + roomId + ' no-go</text></g>';
      });
      svg.innerHTML = lines.join("") + roomNodes.join("") + blocked.join("");
    }

    loadSnapshot();
  </script>
</body>
</html>
"""
```

- [ ] **Step 4: Add the standard-library server**

Create `src/mochi/map_console/server.py`:

```python
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from typing import Any

from mochi.map_console.runtime import MapConsoleRuntime
from mochi.map_console.static import APP_HTML


def create_server(
    runtime: MapConsoleRuntime,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/":
                self._send_html(APP_HTML)
                return
            if self.path == "/api/snapshot":
                self._send_json(runtime.snapshot().model_dump(mode="json"))
                return
            self._send_json({"error": "Not found."}, status=HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            try:
                payload = self._read_json()
                text = payload.get("text", "")
                if not isinstance(text, str):
                    raise ValueError("text must be a string.")
                if self.path == "/api/command":
                    snapshot = runtime.handle_command(text)
                    self._send_json(snapshot.model_dump(mode="json"))
                    return
                if self.path == "/api/voice-turn":
                    snapshot = runtime.handle_voice_text(text)
                    self._send_json(snapshot.model_dump(mode="json"))
                    return
                self._send_json({"error": "Not found."}, status=HTTPStatus.NOT_FOUND)
            except (json.JSONDecodeError, ValueError) as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)

        def log_message(self, format: str, *args: object) -> None:
            return

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length).decode("utf-8")
            if not raw_body:
                return {}
            payload = json.loads(raw_body)
            if not isinstance(payload, dict):
                raise ValueError("JSON body must be an object.")
            return payload

        def _send_html(self, html: str) -> None:
            encoded = html.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _send_json(
            self,
            payload: dict[str, Any],
            *,
            status: HTTPStatus = HTTPStatus.OK,
        ) -> None:
            encoded = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return ThreadingHTTPServer((host, port), Handler)
```

- [ ] **Step 5: Export server helper**

Update `src/mochi/map_console/__init__.py`:

```python
from mochi.map_console.history import MovementHistory
from mochi.map_console.models import ConsoleTurn, MapSnapshot, MovementEvent, RoomSnapshot
from mochi.map_console.runtime import MapConsoleRuntime
from mochi.map_console.server import create_server
from mochi.map_console.snapshot import build_map_snapshot

__all__ = [
    "ConsoleTurn",
    "MapConsoleRuntime",
    "MapSnapshot",
    "MovementEvent",
    "MovementHistory",
    "RoomSnapshot",
    "build_map_snapshot",
    "create_server",
]
```

- [ ] **Step 6: Run server tests**

Run:

```bash
pytest tests/test_map_console_server.py -v
```

Expected: all tests in `tests/test_map_console_server.py` pass.

- [ ] **Step 7: Commit**

```bash
git add src/mochi/map_console tests/test_map_console_server.py
git commit -m "Add local map console server"
```

---

### Task 6: Add CLI Voice And Map UI Commands

**Files:**
- Modify: `src/mochi/cli/main.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add failing CLI tests**

Update `tests/test_cli.py`:

```python
def test_help_lists_v02_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in ("voice", "map-ui"):
        assert command in result.stdout


def test_voice_command_runs_fake_voice_turn() -> None:
    result = invoke_cli(["voice", "where are you?"])

    assert result.exit_code == 0
    assert "Recognized" in result.stdout
    assert "where are you?" in result.stdout
    assert "Spoken" in result.stdout
    assert "living_room" in result.stdout


def test_voice_command_moves_fake_robot() -> None:
    result = invoke_cli(["voice", "go to kitchen"])

    assert result.exit_code == 0
    assert "go to kitchen" in result.stdout
    assert "kitchen" in result.stdout
    assert "succeeded" in result.stdout


def test_map_ui_command_prints_url_without_serving_forever() -> None:
    result = invoke_cli(["map-ui", "--dry-run"])

    assert result.exit_code == 0
    assert "http://127.0.0.1:8765" in result.stdout
    assert "Mochi map console" in result.stdout
```

- [ ] **Step 2: Run CLI tests to verify they fail**

Run:

```bash
pytest tests/test_cli.py::test_help_lists_v02_commands tests/test_cli.py::test_voice_command_runs_fake_voice_turn tests/test_cli.py::test_voice_command_moves_fake_robot tests/test_cli.py::test_map_ui_command_prints_url_without_serving_forever -v
```

Expected: fail because the new commands do not exist.

- [ ] **Step 3: Update CLI imports and runtime**

Modify `src/mochi/cli/main.py` imports:

```python
from mochi.core.models import ActionCommand, HouseMap, PeopleConfig, RobotProfile
from mochi.map_console.runtime import MapConsoleRuntime
from mochi.map_console.server import create_server
from mochi.voice.engine import VoiceEngine
from mochi.voice.fake import FakeSpeechRecognizer, FakeSpeechSynthesizer
```

Update the `Runtime` dataclass:

```python
@dataclass(frozen=True)
class Runtime:
    robot_profile: RobotProfile
    house_map: HouseMap
    people: PeopleConfig
    state: RobotState
    memory_store: MemoryStore
    navigator: FakeNavigator
    action_router: ActionRouter
    prompt_builder: PersonalityPromptBuilder
    llm: FakeLLM
    engine: ConversationEngine
```

Update the `return Runtime(...)` block in `build_runtime`:

```python
    return Runtime(
        robot_profile=robot_profile,
        house_map=house_map,
        people=people,
        state=state,
        memory_store=memory_store,
        navigator=navigator,
        action_router=action_router,
        prompt_builder=prompt_builder,
        llm=llm,
        engine=engine,
    )
```

- [ ] **Step 4: Add CLI voice command**

Add this command to `src/mochi/cli/main.py`:

```python
@app.command()
def voice(message: str) -> None:
    """Run one fake voice turn through Mochi."""
    runtime = build_runtime()
    synthesizer = FakeSpeechSynthesizer()
    voice_engine = VoiceEngine(
        conversation_engine=runtime.engine,
        recognizer=FakeSpeechRecognizer([message]),
        synthesizer=synthesizer,
    )

    try:
        result = voice_engine.handle_turn()
    except ValueError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=2) from error

    table = Table(title="Mochi Fake Voice Turn")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value")
    table.add_row("Recognized", result.input.text)
    table.add_row("Response", result.response_text)
    table.add_row("Spoken", result.output.text)
    if result.actions:
        action_summary = ", ".join(
            "succeeded" if action.succeeded else "failed" for action in result.actions
        )
        table.add_row("Actions", action_summary)
    console.print(table)
```

- [ ] **Step 5: Add CLI map UI command**

Add this command to `src/mochi/cli/main.py`:

```python
@app.command("map-ui")
def map_ui(
    host: str = "127.0.0.1",
    port: int = 8765,
    dry_run: bool = False,
) -> None:
    """Start the local Mochi map console."""
    runtime = build_runtime()
    console_runtime = MapConsoleRuntime(
        house_map=runtime.house_map,
        state=runtime.state,
        conversation_engine=runtime.engine,
    )
    url = f"http://{host}:{port}"
    console.print(f"Mochi map console: {url}")
    if dry_run:
        return

    try:
        server = create_server(console_runtime, host=host, port=port)
    except OSError as error:
        console.print(f"[red]Could not start map console on {url}: {error}[/red]")
        raise typer.Exit(code=1) from error

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        console.print()
    finally:
        server.server_close()
```

- [ ] **Step 6: Run focused CLI tests**

Run:

```bash
pytest tests/test_cli.py -v
```

Expected: all tests in `tests/test_cli.py` pass.

- [ ] **Step 7: Commit**

```bash
git add src/mochi/cli/main.py tests/test_cli.py
git commit -m "Add v02 voice and map UI commands"
```

---

### Task 7: Add v0.2 Acceptance Tests And README Updates

**Files:**
- Create: `tests/test_v02_acceptance.py`
- Modify: `README.md`

- [ ] **Step 1: Add failing v0.2 acceptance tests**

Create `tests/test_v02_acceptance.py`:

```python
import json
import threading
from http.client import HTTPConnection

from typer.testing import CliRunner

from mochi.cli.main import app, build_runtime
from mochi.map_console.runtime import MapConsoleRuntime
from mochi.map_console.server import create_server

runner = CliRunner()


def test_v02_voice_acceptance_flow() -> None:
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["voice", "go to kitchen"],
            env={"MOCHI_MEMORY_PATH": "memory.sqlite3"},
        )

    assert result.exit_code == 0
    assert "Recognized" in result.stdout
    assert "go to kitchen" in result.stdout
    assert "Spoken" in result.stdout
    assert "kitchen" in result.stdout


def test_v02_map_console_acceptance_flow() -> None:
    runtime = build_runtime()
    console_runtime = MapConsoleRuntime(
        house_map=runtime.house_map,
        state=runtime.state,
        conversation_engine=runtime.engine,
    )
    server = create_server(console_runtime, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        status, snapshot = post_json(
            server.server_port,
            "/api/command",
            {"text": "go to kitchen"},
        )
        blocked_status, blocked_snapshot = post_json(
            server.server_port,
            "/api/command",
            {"text": "go to bedroom"},
        )
    finally:
        server.shutdown()
        server.server_close()

    assert status == 200
    assert snapshot["current_location"] == "kitchen"
    assert blocked_status == 200
    assert blocked_snapshot["current_location"] == "kitchen"
    assert blocked_snapshot["movements"][-1]["requested_destination"] == "bedroom"
    assert blocked_snapshot["movements"][-1]["succeeded"] is False


def post_json(port: int, path: str, payload: dict):
    connection = HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(
            "POST",
            path,
            body=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        body = json.loads(response.read().decode("utf-8"))
        return response.status, body
    finally:
        connection.close()
```

- [ ] **Step 2: Run acceptance tests**

Run:

```bash
pytest tests/test_v02_acceptance.py -v
```

Expected: pass if Tasks 1-6 are complete.

- [ ] **Step 3: Update README current phase**

Replace the first paragraph and bullets under "Current Phase" in `README.md` with this text:

```markdown
v0.2 is software-only. It includes the v0.1 text brain plus:

- Fake voice input and output seams.
- A simulated voice command path through the conversation engine.
- A local browser map console for fake navigation state.
- Movement history for successful and blocked fake moves.
```

Keep the explicit exclusion list and update it to include:

```markdown
v0.2 does not include real robot hardware, ROS, cameras, microphones, motors,
live audio capture, real speaker output, webcam awareness, autonomous background
loops, or Home Assistant.
```

- [ ] **Step 4: Document new commands**

Add these command examples to `README.md`:

````markdown
Run one fake voice turn:

```bash
mochi voice "go to kitchen"
```

Start the local map console:

```bash
mochi map-ui
```
````

- [ ] **Step 5: Update roadmap**

Update the roadmap:

```markdown
- v0.2: Fake voice seams and local map console.
- v0.3: Voice input/output provider experiment.
- v0.4: Webcam awareness.
- v0.5: Autonomous loop.
- v0.6: Home Assistant integration.
- v0.7: ROS/Gazebo simulation.
- v1.0: Real hardware adapter.
```

- [ ] **Step 6: Run README-related tests**

Run:

```bash
pytest tests/test_v02_acceptance.py tests/test_cli.py -v
```

Expected: all selected tests pass.

- [ ] **Step 7: Commit**

```bash
git add README.md tests/test_v02_acceptance.py
git commit -m "Document v02 voice map console"
```

---

### Task 8: Final Verification And Manual UI Check

**Files:**
- No code files should be changed in this task unless verification finds a bug.

- [ ] **Step 1: Run the full test suite**

Run:

```bash
pytest
```

Expected: all tests pass.

- [ ] **Step 2: Run lint**

Run:

```bash
ruff check .
```

Expected: `All checks passed!`

- [ ] **Step 3: Run formatting check or formatting command**

Run:

```bash
ruff format .
```

Expected: files are either unchanged or reformatted cleanly. If files are reformatted, run `pytest` and `ruff check .` again.

- [ ] **Step 4: Start the map console manually**

Run:

```bash
MOCHI_MEMORY_PATH="$(mktemp -t mochi-memory.XXXXXX.sqlite3)" mochi map-ui --port 8765
```

Expected: terminal prints `Mochi map console: http://127.0.0.1:8765` and the server stays running.

- [ ] **Step 5: Verify browser behavior**

Open:

```text
http://127.0.0.1:8765
```

Expected:

- the map renders with Living Room, Kitchen, Charging Corner, and the bedroom no-go zone;
- state shows current location `living_room`;
- running `go to kitchen` updates current location to `kitchen`;
- running `go to bedroom` records a blocked movement and leaves location unchanged;
- using the fake voice field with `where are you?` appends a voice turn.

- [ ] **Step 6: Stop the server**

Press:

```text
Ctrl-C
```

Expected: the command exits without a traceback.

- [ ] **Step 7: Check final git status**

Run:

```bash
git status --short --branch
```

Expected: clean working tree on `codex/v0.2-voice-io`.

- [ ] **Step 8: Push the branch**

Run:

```bash
git push
```

Expected: branch pushes to `origin/codex/v0.2-voice-io`.

---

## Self-Review Notes

- Spec coverage: fake voice interfaces are covered in Task 2; local map console models, history, runtime, and server are covered in Tasks 3-5; CLI commands are covered in Task 6; README and acceptance criteria are covered in Task 7; full verification and browser validation are covered in Task 8.
- Scope check: the plan keeps real microphone input, real speaker output, cameras, robot hardware, ROS, Home Assistant, and autonomous loops out of v0.2.
- Type consistency: `MapConsoleRuntime`, `MovementHistory`, `VoiceEngine`, `SpeechInput`, `SpeechOutput`, `VoiceTurnResult`, `MapSnapshot`, `ConsoleTurn`, and `MovementEvent` names are introduced before later tasks use them.
