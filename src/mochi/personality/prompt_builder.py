from collections.abc import Iterable

from mochi.core.models import PeopleConfig, RobotProfile
from mochi.core.state import RobotState
from mochi.memory.models import Memory
from mochi.personality.mood import describe_mood
from mochi.personality.rules import format_rules


class PersonalityPromptBuilder:
    def __init__(self, profile: RobotProfile) -> None:
        self.profile = profile

    def build(
        self,
        state: RobotState,
        people: PeopleConfig,
        person_id: str | None,
        relevant_memories: Iterable[Memory],
        available_actions: Iterable[str],
    ) -> str:
        sections = [
            self._section("robot", [f"name: {self.profile.name}"]),
            self._section(
                "personality",
                [
                    f"vibe: {self.profile.personality.vibe}",
                    f"mood: {describe_mood(state.mood)}",
                    f"energy_level: {self.profile.personality.energy_level}",
                    f"humor_style: {self.profile.personality.humor_style}",
                    f"talkativeness: {self.profile.personality.talkativeness}",
                ],
            ),
            self._section("rules", [format_rules(self.profile.rules)]),
            self._section("catchphrases", self._format_list(self.profile.catchphrases)),
            self._section(
                "state",
                [
                    f"name: {state.name}",
                    f"location: {state.location}",
                    f"battery_percent: {state.battery_percent}",
                    f"privacy_mode: {state.privacy_mode}",
                    f"active_person: {state.active_person}",
                    f"last_action: {state.last_action}",
                ],
            ),
            self._section(
                "current person",
                self._format_person(person_id=person_id, people=people),
            ),
            self._section("memories", self._format_memories(relevant_memories)),
            self._section("actions", self._format_list(available_actions)),
        ]

        return "\n\n".join(sections)

    def _section(self, title: str, lines: Iterable[str]) -> str:
        return "\n".join([f"[{title}]", *lines])

    def _format_list(self, items: Iterable[str]) -> list[str]:
        values = list(items)
        if not values:
            return ["- none"]

        return [f"- {item}" for item in values]

    def _format_person(self, person_id: str | None, people: PeopleConfig) -> list[str]:
        if person_id is None:
            return ["person_id: none", "status: no current person"]

        person = people.people.get(person_id)
        if person is None:
            return [f"person_id: {person_id}", "status: unknown person"]

        lines = [
            f"person_id: {person_id}",
            f"display_name: {person.display_name}",
            f"relationship: {person.relationship}",
        ]
        greeting_style = getattr(person, "greeting_style", None)
        if greeting_style:
            lines.append(f"greeting_style: {greeting_style}")
        if person.notes:
            lines.extend(f"note: {note}" for note in person.notes)

        return lines

    def _format_memories(self, memories: Iterable[Memory]) -> list[str]:
        values = list(memories)
        if not values:
            return ["- none"]

        return [
            (
                f"- id: {memory.id}; person_id: {memory.person_id}; importance: "
                f"{memory.importance}; created_at: {memory.created_at.isoformat()}; "
                f"content: {memory.content}"
            )
            for memory in values
        ]
