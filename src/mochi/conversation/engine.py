from typing import Protocol

from pydantic import BaseModel, Field

from mochi.actions.action_router import ActionRouter
from mochi.conversation.llm_client import LLMClient
from mochi.core.models import ActionCommand, ActionResult, PeopleConfig
from mochi.core.state import RobotState
from mochi.memory.store import MemoryStore
from mochi.personality.prompt_builder import PersonalityPromptBuilder


class ConversationResponse(BaseModel):
    text: str
    actions: list[ActionResult] = Field(default_factory=list)


class PromptBuilder(Protocol):
    def build(
        self,
        state: RobotState,
        people: PeopleConfig,
        person_id: str | None,
        relevant_memories: object,
        available_actions: object,
    ) -> str:
        """Build a system prompt for the LLM."""
        ...


class ConversationEngine:
    def __init__(
        self,
        *,
        state: RobotState,
        memory_store: MemoryStore,
        action_router: ActionRouter,
        prompt_builder: PersonalityPromptBuilder,
        llm: LLMClient,
        people: PeopleConfig,
    ) -> None:
        self.state = state
        self.memory_store = memory_store
        self.action_router = action_router
        self.prompt_builder = prompt_builder
        self.llm = llm
        self.people = people

    def respond(self, user_message: str, person_id: str | None = None) -> ConversationResponse:
        stripped_message = user_message.strip()
        command_text = stripped_message.lower()
        command_text_without_question = command_text.rstrip("?")

        if command_text == "remember that":
            return ConversationResponse(text="Tell me what to remember.")

        if command_text.startswith("remember that "):
            content = stripped_message[len("remember that ") :].strip()
            return self._execute(
                ActionCommand(
                    type="remember",
                    payload={"person_id": person_id or "global", "content": content},
                ),
                success_text="Noted. I saved that memory.",
            )

        if command_text == "forget memory":
            return ConversationResponse(text="Tell me the memory id to forget.")

        if command_text.startswith("forget memory "):
            memory_id = stripped_message[len("forget memory ") :].strip()
            return self._execute(
                ActionCommand(type="forget", payload={"memory_id": memory_id}),
                success_text="Forgotten.",
            )

        if command_text == "memories":
            return ConversationResponse(text=self._format_memories(person_id))

        if command_text_without_question == "where are you":
            return ConversationResponse(text=f"I am in {self.state.location}.")

        if command_text == "go to":
            return ConversationResponse(text="Tell me where to go.")

        if command_text.startswith("go to "):
            room = command_text[len("go to ") :].strip()
            return self._execute(ActionCommand(type="move", payload={"room": room}))

        if command_text == "go charge":
            return self._execute(ActionCommand(type="dock"))

        if command_text == "privacy mode on":
            return self._execute(
                ActionCommand(type="privacy_on"),
                success_text="Privacy mode enabled.",
            )

        if command_text == "privacy mode off":
            return self._execute(
                ActionCommand(type="privacy_off"),
                success_text="Privacy mode disabled.",
            )

        prompt = self.prompt_builder.build(
            state=self.state,
            people=self.people,
            person_id=person_id,
            relevant_memories=self._relevant_memories(person_id),
            available_actions=self._available_actions(),
        )
        return ConversationResponse(text=self.llm.generate(prompt, user_message))

    def _execute(
        self,
        command: ActionCommand,
        *,
        success_text: str | None = None,
    ) -> ConversationResponse:
        result = self.action_router.execute(command)
        text = success_text if result.succeeded and success_text is not None else result.message
        return ConversationResponse(text=text, actions=[result])

    def _relevant_memories(self, person_id: str | None) -> object:
        if person_id is None or person_id not in self.people.people:
            return []
        return self.memory_store.search_memories(person_id=person_id)

    def _visible_memories(self, person_id: str | None) -> object:
        if person_id is None:
            return self.memory_store.search_memories(person_id="global")
        if person_id in self.people.people:
            return self.memory_store.search_memories(person_id=person_id)
        return []

    def _format_memories(self, person_id: str | None) -> str:
        memories = self._visible_memories(person_id)
        if not memories:
            return "No memories saved."
        return "\n".join(f"{memory.id}: {memory.content}" for memory in memories)

    def _available_actions(self) -> list[str]:
        return [
            "move",
            "dock",
            "remember",
            "forget",
            "privacy_on",
            "privacy_off",
            "set_mood",
        ]
