# Conversation Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement text conversation handling with simple command detection before LLM fallback.

**Architecture:** `ConversationEngine` receives dependencies through its constructor: state, memory store, action router, prompt builder, LLM client, and people config. Commands become `ActionCommand`s and normal text goes through prompt builder plus LLM client.

**Tech Stack:** Pydantic, pytest, ruff.

---

### Task 1: Engine Commands and LLM Fallback

**Files:**
- Create: `src/mochi/conversation/engine.py`
- Test: `tests/test_conversation_engine.py`

- [x] **Step 1: Write tests**

```python
from collections.abc import Callable

import pytest

from mochi.actions.action_router import ActionRouter
from mochi.core.models import HouseMap, PeopleConfig, PersonProfile, PersonalityConfig, RobotProfile, Room
from mochi.core.state import RobotState
from mochi.conversation.engine import ConversationEngine
from mochi.conversation.fake_llm import FakeLLM
from mochi.memory.store import MemoryStore
from mochi.navigation.fake_navigator import FakeNavigator
from mochi.personality.prompt_builder import PersonalityPromptBuilder


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
    assert engine.respond(f"forget memory {memory_id}", person_id="daniela").actions[0].succeeded is True


def test_engine_moves_and_blocks_no_go_zone(engine: ConversationEngine) -> None:
    assert "kitchen" in engine.respond("go to kitchen", person_id="daniela").text
    assert "no-go zone" in engine.respond("go to bedroom", person_id="daniela").text


def test_engine_toggles_privacy(engine: ConversationEngine) -> None:
    assert "enabled" in engine.respond("privacy mode on", person_id="daniela").text
    assert "disabled" in engine.respond("privacy mode off", person_id="daniela").text


def test_engine_uses_llm_for_normal_conversation(engine_factory) -> None:
    engine = engine_factory(llm=FakeLLM(response="Tiny robot brain engaged."))
    assert engine.respond("hello", person_id="daniela").text == "Tiny robot brain engaged."
```

- [x] **Step 2: Run tests to verify red**

Run: `pytest tests/test_conversation_engine.py -v`

Expected: failure for missing `ConversationEngine` or response model.

- [x] **Step 3: Implement response model**

Create `ConversationResponse` with:

```python
text: str
actions: list[ActionResult] = Field(default_factory=list)
```

- [x] **Step 4: Implement command detection**

Before LLM calls, detect lowercased stripped messages:
- `remember that <content>` -> remember action.
- `forget memory <id>` -> forget action.
- `where are you` -> report `state.location`.
- `go to <room>` -> move action.
- `go charge` -> dock action.
- `privacy mode on` -> privacy_on action.
- `privacy mode off` -> privacy_off action.

- [x] **Step 5: Implement normal conversation path**

Build prompt with current state, person, memories from `MemoryStore.search_memories(person_id=person_id)`, and available actions. Call `llm.generate(prompt, user_message)` and return the generated text with no actions.

- [x] **Step 6: Run verification**

Run: `pytest tests/test_conversation_engine.py -v`

Expected: all tests pass.

Run: `pytest && ruff check .`

Expected: all tests and lint checks pass.
