# Personality Prompt Builder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build system prompts from profile config, state, person context, memories, and available fake actions.

**Architecture:** Keep prompt assembly deterministic and testable in `personality/prompt_builder.py`. Put small helper functions for rules and mood in their own modules.

**Tech Stack:** Pydantic models, pytest, ruff.

---

### Task 1: Prompt Assembly

**Files:**
- Create: `src/mochi/personality/__init__.py`
- Create: `src/mochi/personality/prompt_builder.py`
- Create: `src/mochi/personality/rules.py`
- Create: `src/mochi/personality/mood.py`
- Test: `tests/test_personality_prompt_builder.py`

- [x] **Step 1: Write tests**

```python
from datetime import UTC, datetime

from mochi.core.models import PeopleConfig, PersonProfile, PersonalityConfig, RobotProfile
from mochi.core.state import RobotState
from mochi.memory.models import Memory
from mochi.personality.prompt_builder import PersonalityPromptBuilder


def test_prompt_includes_profile_state_person_memories_and_actions() -> None:
    profile = RobotProfile(
        name="Mochi",
        personality=PersonalityConfig(vibe="playful", energy_level="medium", humor_style="dry", talkativeness="low"),
        rules=["Do not pretend to have real hardware in v0.1."],
        catchphrases=["Tiny robot brain engaged."],
    )
    people = PeopleConfig(people={"daniela": PersonProfile(display_name="Daniela", relationship="owner/friend", greeting_style="warm")})
    state = RobotState(name="Mochi", location="kitchen", battery_percent=42, privacy_mode=True)
    memories = [Memory(id="m1", person_id="daniela", content="likes quiet mode", importance=3, created_at=datetime.now(UTC))]

    prompt = PersonalityPromptBuilder(profile).build(
        state=state,
        people=people,
        person_id="daniela",
        relevant_memories=memories,
        available_actions=["speak", "move", "remember", "privacy_on"],
    )

    assert "playful" in prompt
    assert "privacy_mode: True" in prompt
    assert "location: kitchen" in prompt
    assert "battery_percent: 42" in prompt
    assert "Daniela" in prompt
    assert "likes quiet mode" in prompt
    assert "move" in prompt
```

- [x] **Step 2: Run tests to verify red**

Run: `pytest tests/test_personality_prompt_builder.py -v`

Expected: failure for missing personality modules.

- [x] **Step 3: Implement prompt builder**

`PersonalityPromptBuilder.build()` should accept `state`, `people`, `person_id`, `relevant_memories`, and `available_actions`, then return a newline-delimited prompt with sections: robot, personality, rules, catchphrases, state, current person, memories, actions.

- [x] **Step 4: Implement helper modules**

`rules.py` should expose `format_rules(rules: list[str]) -> str`.

`mood.py` should expose `describe_mood(mood: str) -> str` with direct mappings for `curious`, `playful`, `calm`, and default `mood`.

- [x] **Step 5: Run verification**

Run: `pytest tests/test_personality_prompt_builder.py -v`

Expected: all tests pass.

Run: `pytest && ruff check .`

Expected: all tests and lint checks pass.
