# Previous Work - 05/31/26

## Session

- Project: Mochi Robot Brain, software-first robot brain for a future home robot.
- Workspace: `/Users/briantirado/Daniela`
- Branch: `main` tracking `origin/main`
- Status at memory capture: working tree has uncommitted v0.1 scaffold changes and this memory file.

## Completed Work

- Added repo agent guidance for Mochi in `AGENTS.md`, including software-only scope, v0.1 target, architecture rules, privacy rules, Previous Work Memory, and Lessons Learned instructions.
- Created initial memory guidance in `Agent.md`.
- Created the initial Python 3.11+ repo scaffold:
  - `README.md`
  - `pyproject.toml`
  - `.env.example`
  - `.gitignore`
  - `config/robot_profile.yaml`
  - `config/house_map.yaml`
  - `config/people.yaml`
  - `src/mochi/`
  - `tests/`
- Created detailed implementation plans in `docs/superpowers/plans/` and completed the v0.1 sequence.
- Implemented a text-only Mochi v0.1 with:
  - Typer and Rich terminal CLI.
  - YAML config loading with Pydantic validation.
  - Fake robot state.
  - Fake navigation with no-go zones and dock fallback.
  - Local SQLite memory store.
  - Explicit memory add/list/search/delete flows.
  - Personality prompt builder, mood helpers, and conversation rules.
  - LLM abstraction with fake test client and OpenAI shell adapter.
  - Action router with fake move/speak/privacy actions.
  - Conversation engine for basic text commands and fake LLM fallback.
  - Behavior planner that suggests actions but does not run a proactive loop.
  - CLI commands for `chat`, `state`, `memories`, `forget`, and `privacy`.

## Changed Files

- Top-level project files:
  - `AGENTS.md`
  - `Agent.md`
  - `README.md`
  - `pyproject.toml`
  - `.env.example`
  - `.gitignore`
- Config:
  - `config/robot_profile.yaml`
  - `config/house_map.yaml`
  - `config/people.yaml`
- Source package:
  - `src/mochi/__init__.py`
  - `src/mochi/__main__.py`
  - `src/mochi/cli/__init__.py`
  - `src/mochi/cli/main.py`
  - `src/mochi/core/models.py`
  - `src/mochi/core/settings.py`
  - `src/mochi/core/state.py`
  - `src/mochi/navigation/base.py`
  - `src/mochi/navigation/fake_navigator.py`
  - `src/mochi/memory/models.py`
  - `src/mochi/memory/store.py`
  - `src/mochi/conversation/llm_client.py`
  - `src/mochi/conversation/fake_llm.py`
  - `src/mochi/conversation/openai_llm.py`
  - `src/mochi/conversation/engine.py`
  - `src/mochi/personality/prompt_builder.py`
  - `src/mochi/personality/rules.py`
  - `src/mochi/personality/mood.py`
  - `src/mochi/actions/action_router.py`
  - `src/mochi/actions/speak.py`
  - `src/mochi/actions/move.py`
  - `src/mochi/actions/privacy.py`
  - `src/mochi/behavior/planner.py`
  - `src/mochi/behavior/policies.py`
  - Compatibility shims: `src/mochi/config.py`, `src/mochi/models.py`, `src/mochi/state.py`
- Tests:
  - `tests/test_cli.py`
  - `tests/test_config.py`
  - `tests/test_config_loading.py`
  - `tests/test_robot_state.py`
  - `tests/test_fake_navigation.py`
  - `tests/test_robot.py`
  - `tests/test_memory.py`
  - `tests/test_memory_store.py`
  - `tests/test_llm_client.py`
  - `tests/test_personality_prompt_builder.py`
  - `tests/test_action_router.py`
  - `tests/test_conversation_engine.py`
  - `tests/test_behavior_planner.py`
  - `tests/test_v01_acceptance.py`

## Verification

- Installed development dependencies into `.venv` because the system Python is externally managed.
- Use this environment prefix for local commands:

```bash
PATH="$PWD/.venv/bin:$PATH"
```

- Final verification passed:

```bash
pytest
# 73 passed

ruff check .
# All checks passed!
```

- CLI smoke test was run with:

```bash
PATH="$PWD/.venv/bin:$PATH" mochi --help
printf "where are you?\ngo to kitchen\nremember that I like quiet mode after work\nmemories\nprivacy mode on\ngo to bedroom\nexit\n" | PATH="$PWD/.venv/bin:$PATH" mochi chat
```

- Smoke output confirmed:
  - current location reported as `living_room`
  - navigation to `kitchen`
  - explicit memory saved with `Noted`
  - in-chat memory listing showed the saved memory
  - privacy mode enabled
  - no-go zone blocked `bedroom`

## Bugs Fixed

- Fixed editable CLI wrapper compatibility after moving CLI code into a package by re-exporting `app` and callable `main` from `src/mochi/cli/__init__.py`.
- Removed hardcoded `Brian` from the `mochi.config` compatibility shim; missing relationship data now raises a path-bearing `ValueError`.
- Fixed `FakeNavigator.go_to` so failed navigation calls do not rebind internal state.
- Added `charging_corner` dock fallback for fake navigation.
- Added explicit SQLite connection closing and transaction handling in `MemoryStore`.
- Removed surprising `Memory.__eq__` dict compatibility and updated tests to assert fields directly.
- Narrowed action payload validation so dependency errors are not swallowed by `ActionRouter`.
- Fixed no-person LLM fallback so it does not expose all memories.
- Fixed in-chat `memories` command scoping:
  - no-person chat sees only `global` memories
  - known-person chat sees only that person's memories
  - unknown-person chat sees none
  - top-level `mochi memories` remains explicit admin/list-all

## Decisions

- Keep v0.1 software-only and text-only.
- Do not add hardware, ROS, camera, microphone, motors, Home Assistant, face recognition, or heavy ML dependencies in v0.1.
- Use fake adapters behind interfaces so later hardware integrations can replace them.
- Only store memories when the user explicitly asks Mochi to remember something.
- Privacy mode suppresses proactive behavior.
- The conversation layer routes structured actions through `ActionRouter`; it does not control hardware directly.
- No git staging, commit, push, or PR was performed in this session.

## Follow-ups

- Decide whether to commit the current v0.1 working tree or open a draft PR.
- Consider v0.2 voice I/O only after v0.1 is committed and stable.
- Consider removing compatibility shims after callers migrate to the new package layout.
- Consider adding type checking later.
- Consider persisted robot state later; current robot state is session-local while memory persists in SQLite.
