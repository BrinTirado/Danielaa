import os


class LLMConfigurationError(RuntimeError):
    pass


class OpenAILLM:
    def __init__(self, api_key: str, model: str | None = None) -> None:
        self.api_key = api_key
        self.model = model

    @classmethod
    def from_env(cls) -> "OpenAILLM":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise LLMConfigurationError("OPENAI_API_KEY is required to use OpenAILLM.")
        return cls(api_key=api_key, model=os.environ.get("OPENAI_MODEL"))

    def generate(self, system_prompt: str, user_message: str) -> str:
        raise NotImplementedError("OpenAILLM network calls are not enabled in v0.1 tests.")
