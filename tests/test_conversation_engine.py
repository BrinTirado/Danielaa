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


class RecordingLLM:
    def __init__(self, response: str = "recorded response") -> None:
        self.response = response
        self.prompts: list[str] = []
        self.messages: list[str] = []

    def generate(self, system_prompt: str, user_message: str) -> str:
        self.prompts.append(system_prompt)
        self.messages.append(user_message)
        return self.response


@pytest.fixture
def engine_factory(tmp_path) -> Callable[..., ConversationEngine]:
    def build_engine(llm=None) -> ConversationEngine:
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
                "living_room": Room(connected_to=["kitchen", "charging_station"]),
                "kitchen": Room(connected_to=["living_room"]),
                "charging_station": Room(connected_to=["living_room"]),
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
            llm=llm or FakeLLM(),
            people=people,
        )

    return build_engine


@pytest.fixture
def engine(engine_factory) -> ConversationEngine:
    return engine_factory()


def test_engine_reports_location(engine: ConversationEngine) -> None:
    response = engine.respond("where are you?", person_id="daniela")
    assert "living_room" in response.text


def test_engine_remembers_and_forgets(engine: ConversationEngine) -> None:
    remembered = engine.respond("remember that I like quiet mode after work", person_id="daniela")
    memory_id = remembered.actions[0].payload["memory_id"]

    assert "Noted" in remembered.text
    forgotten = engine.respond(f"forget memory {memory_id}", person_id="daniela")
    assert forgotten.actions[0].succeeded is True


def test_engine_moves_and_blocks_no_go_zone(engine: ConversationEngine) -> None:
    assert "kitchen" in engine.respond("go to kitchen", person_id="daniela").text
    assert "no-go zone" in engine.respond("go to bedroom", person_id="daniela").text


def test_engine_toggles_privacy(engine: ConversationEngine) -> None:
    assert "enabled" in engine.respond("privacy mode on", person_id="daniela").text
    assert "disabled" in engine.respond("privacy mode off", person_id="daniela").text


def test_engine_uses_llm_for_normal_conversation(engine_factory) -> None:
    engine = engine_factory(llm=FakeLLM(response="Tiny robot brain engaged."))
    assert engine.respond("hello", person_id="daniela").text == "Tiny robot brain engaged."


def test_normal_conversation_does_not_auto_save_memory(engine: ConversationEngine) -> None:
    engine.respond("I like quiet mode after work", person_id="daniela")

    assert engine.memory_store.list_memories() == []


def test_normal_conversation_without_person_does_not_include_all_memories(engine_factory) -> None:
    llm = RecordingLLM()
    engine = engine_factory(llm=llm)
    engine.memory_store.add_memory("daniela", "Daniela likes quiet mode")
    engine.memory_store.add_memory("roommate", "Roommate likes loud music")

    engine.respond("hello")

    assert "Daniela likes quiet mode" not in llm.prompts[0]
    assert "Roommate likes loud music" not in llm.prompts[0]


def test_normal_conversation_only_includes_current_person_memories(engine_factory) -> None:
    llm = RecordingLLM()
    engine = engine_factory(llm=llm)
    engine.memory_store.add_memory("daniela", "Daniela likes quiet mode")
    engine.memory_store.add_memory("roommate", "Roommate likes loud music")

    engine.respond("hello", person_id="daniela")

    assert "Daniela likes quiet mode" in llm.prompts[0]
    assert "Roommate likes loud music" not in llm.prompts[0]


def test_chat_memories_without_person_only_lists_global_memories(
    engine: ConversationEngine,
) -> None:
    engine.memory_store.add_memory("global", "Global session note")
    engine.memory_store.add_memory("daniela", "Daniela likes quiet mode")

    response = engine.respond("memories")

    assert "Global session note" in response.text
    assert "Daniela likes quiet mode" not in response.text


def test_chat_memories_for_known_person_only_lists_that_persons_memories(
    engine: ConversationEngine,
) -> None:
    engine.memory_store.add_memory("global", "Global session note")
    engine.memory_store.add_memory("daniela", "Daniela likes quiet mode")
    engine.memory_store.add_memory("roommate", "Roommate likes loud music")

    response = engine.respond("memories", person_id="daniela")

    assert "Daniela likes quiet mode" in response.text
    assert "Global session note" not in response.text
    assert "Roommate likes loud music" not in response.text


def test_chat_memories_for_unknown_person_reveals_no_memories(
    engine: ConversationEngine,
) -> None:
    engine.memory_store.add_memory("global", "Global session note")
    engine.memory_store.add_memory("daniela", "Daniela likes quiet mode")

    response = engine.respond("memories", person_id="unknown")

    assert response.text == "No memories saved."


@pytest.mark.parametrize(
    ("message", "expected_text"),
    [
        ("remember that ", "what to remember"),
        ("forget memory ", "memory id"),
        ("go to ", "where to go"),
    ],
)
def test_malformed_explicit_commands_return_error_without_successful_action(
    engine_factory,
    message: str,
    expected_text: str,
) -> None:
    llm = RecordingLLM()
    engine = engine_factory(llm=llm)

    response = engine.respond(message, person_id="daniela")

    assert expected_text in response.text.lower()
    assert not any(action.succeeded for action in response.actions)
    assert llm.prompts == []
