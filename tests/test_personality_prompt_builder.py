from datetime import UTC, datetime

from mochi.core.models import PeopleConfig, PersonalityConfig, PersonProfile, RobotProfile
from mochi.core.state import RobotState
from mochi.memory.models import Memory
from mochi.personality.prompt_builder import PersonalityPromptBuilder


def test_prompt_includes_profile_state_person_memories_and_actions() -> None:
    profile = RobotProfile(
        name="Mochi",
        personality=PersonalityConfig(
            vibe="playful", energy_level="medium", humor_style="dry", talkativeness="low"
        ),
        rules=["Do not pretend to have real hardware in v0.1."],
        catchphrases=["Tiny robot brain engaged."],
    )
    people = PeopleConfig(
        people={
            "daniela": PersonProfile(
                display_name="Daniela", relationship="owner/friend", greeting_style="warm"
            )
        }
    )
    state = RobotState(name="Mochi", location="kitchen", battery_percent=42, privacy_mode=True)
    memories = [
        Memory(
            id="m1",
            person_id="daniela",
            content="likes quiet mode",
            importance=3,
            created_at=datetime.now(UTC),
        )
    ]

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
