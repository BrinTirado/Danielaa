import pytest

from mochi.conversation.fake_llm import FakeLLM
from mochi.conversation.openai_llm import LLMConfigurationError, OpenAILLM


def test_fake_llm_returns_deterministic_response() -> None:
    llm = FakeLLM(response="Tiny robot brain engaged.")
    assert llm.generate("prompt", "hello") == "Tiny robot brain engaged."


def test_fake_llm_can_echo_last_user_message() -> None:
    llm = FakeLLM()
    assert llm.generate("prompt", "hello").endswith("hello")


def test_openai_llm_requires_api_key_when_selected(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(LLMConfigurationError, match="OPENAI_API_KEY"):
        OpenAILLM.from_env()
