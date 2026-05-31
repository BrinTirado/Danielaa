# LLM Client Abstraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an offline-first LLM interface with deterministic fake responses and optional OpenAI configuration.

**Architecture:** The conversation engine depends on the `LLMClient` protocol, not a concrete provider. `FakeLLM` is used in tests. `OpenAILLM` raises a clear configuration error when selected without required environment.

**Tech Stack:** Protocols, dataclasses or Pydantic, pytest, ruff.

---

### Task 1: LLM Protocol and Fake Provider

**Files:**
- Create: `src/mochi/conversation/__init__.py`
- Create: `src/mochi/conversation/llm_client.py`
- Create: `src/mochi/conversation/fake_llm.py`
- Create: `src/mochi/conversation/openai_llm.py`
- Test: `tests/test_llm_client.py`

- [x] **Step 1: Write tests**

```python
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
```

- [x] **Step 2: Run tests to verify red**

Run: `pytest tests/test_llm_client.py -v`

Expected: failures for missing conversation modules.

- [x] **Step 3: Implement `LLMClient` protocol**

`llm_client.py`:

```python
from typing import Protocol


class LLMClient(Protocol):
    def generate(self, system_prompt: str, user_message: str) -> str:
        """Return one assistant response."""
```

- [x] **Step 4: Implement `FakeLLM`**

Default behavior: return `Fake Mochi response to: {user_message}`. If constructed with `response`, always return that response.

- [x] **Step 5: Implement `OpenAILLM` configuration shell**

`OpenAILLM.from_env()` should read `OPENAI_API_KEY` and optional `OPENAI_MODEL`. If the key is absent, raise `LLMConfigurationError("OPENAI_API_KEY is required to use OpenAILLM.")`. The `generate()` method can raise `NotImplementedError("OpenAILLM network calls are not enabled in v0.1 tests.")` until the user asks for real API wiring.

- [x] **Step 6: Run verification**

Run: `pytest tests/test_llm_client.py -v`

Expected: all tests pass.

Run: `pytest && ruff check .`

Expected: all tests and lint checks pass.
