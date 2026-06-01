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
