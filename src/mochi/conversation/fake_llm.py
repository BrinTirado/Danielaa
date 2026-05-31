class FakeLLM:
    def __init__(self, response: str | None = None) -> None:
        self.response = response

    def generate(self, system_prompt: str, user_message: str) -> str:
        if self.response is not None:
            return self.response
        return f"Fake Mochi response to: {user_message}"
