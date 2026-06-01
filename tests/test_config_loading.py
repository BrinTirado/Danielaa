from pathlib import Path

import pytest

from mochi.core.settings import (
    ConfigError,
    load_house_map,
    load_people_config,
    load_robot_profile,
)

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
    assert house_map.rooms["living_room"].map_position is not None
    assert house_map.rooms["living_room"].map_position.x == 160
    assert house_map.rooms["living_room"].map_position.y == 160


def test_load_people_config() -> None:
    people = load_people_config(CONFIG_DIR / "people.yaml")
    assert people.people["daniela"].display_name == "Daniela"


def test_invalid_config_raises_clear_error(tmp_path) -> None:
    path = tmp_path / "robot_profile.yaml"
    path.write_text("name: 123\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="robot_profile.yaml"):
        load_robot_profile(path)
