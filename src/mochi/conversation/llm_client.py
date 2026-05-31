from typing import Protocol


class LLMClient(Protocol):
    def generate(self, system_prompt: str, user_message: str) -> str:
        """Return one assistant response."""
        ...
