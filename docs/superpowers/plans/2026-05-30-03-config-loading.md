# Config Loading Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Load Mochi YAML configuration into validated Pydantic models with clear errors.

**Architecture:** Put domain models in `src/mochi/core/models.py` and file/environment loading in `src/mochi/core/settings.py`. Existing flat modules can become compatibility shims or be migrated once tests import the new paths.

**Tech Stack:** Pydantic, PyYAML, pytest, ruff.

---

### Task 1: Core Config Models

**Files:**
- Create: `src/mochi/core/__init__.py`
- Create: `src/mochi/core/models.py`
- Create: `src/mochi/core/settings.py`
- Modify: `config/robot_profile.yaml`
- Modify: `config/house_map.yaml`
- Modify: `config/people.yaml`
- Test: `tests/test_config_loading.py`

- [x] **Step 1: Write valid config tests**

```python
from pathlib import Path

from mochi.core.settings import load_house_map, load_people_config, load_robot_profile


CONFIG_DIR = Path("config")


def test_load_robot_profile() -> None:
    profile = load_robot_profile(CONFIG_DIR / "robot_profile.yaml")
    assert profile.name == "Mochi"
    assert profile.personality.vibe
    assert "Do not pretend to have real hardware in v0.1." in profile.rules


def test_load_house_map() -> None:
    house_map = load_house_map(CONFIG_DIR / "house_map.yaml")
    assert house_map.default_location == "living_room"
    assert "kitchen" in house_map.rooms
    assert "bedroom" in house_map.no_go_zones


def test_load_people_config() -> None:
    people = load_people_config(CONFIG_DIR / "people.yaml")
    assert people.people["daniela"].display_name == "Daniela"
```

- [x] **Step 2: Write invalid config test**

```python
import pytest

from mochi.core.settings import ConfigError, load_robot_profile


def test_invalid_config_raises_clear_error(tmp_path) -> None:
    path = tmp_path / "robot_profile.yaml"
    path.write_text("name: 123\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="robot_profile.yaml"):
        load_robot_profile(path)
```

- [x] **Step 3: Run tests to verify red**

Run: `pytest tests/test_config_loading.py -v`

Expected: failures for missing `mochi.core.settings` or missing model fields.

- [x] **Step 4: Implement models**

Create Pydantic models for `RobotProfile`, `PersonalityConfig`, `HouseMap`, `Room`, `PeopleConfig`, and `PersonProfile`. Use `dict[str, Room]` for rooms and `dict[str, PersonProfile]` for people to match the YAML.

- [x] **Step 5: Implement loaders**

`settings.py` should define:

```python
class ConfigError(ValueError):
    pass


def load_robot_profile(path: Path) -> RobotProfile: ...
def load_house_map(path: Path) -> HouseMap: ...
def load_people_config(path: Path) -> PeopleConfig: ...
```

Each function should read YAML as a mapping and wrap Pydantic/YAML failures in `ConfigError(f"Invalid config in {path}: {error}")`.

- [x] **Step 6: Run verification**

Run: `pytest tests/test_config_loading.py -v`

Expected: all tests pass.

Run: `pytest && ruff check .`

Expected: all tests and lint checks pass.
