from pathlib import Path

import pytest

from mochi.config import load_house_map, load_people, load_robot_profile

CONFIG_DIR = Path("config")


def test_load_robot_profile_reads_personality() -> None:
    profile = load_robot_profile(CONFIG_DIR / "robot_profile.yaml")

    assert profile.name == "Mochi"
    assert profile.version == "0.1"
    assert profile.personality.tone == "warm, curious, and gently playful"
    assert profile.capabilities.hardware_enabled is False


def test_load_house_map_reads_rooms_and_start_location() -> None:
    house_map = load_house_map(CONFIG_DIR / "house_map.yaml")

    room_names = {room.name for room in house_map.rooms}
    assert house_map.home_name == "Mochi House"
    assert house_map.start_location == "living_room"
    assert {"living_room", "kitchen", "charging_corner"}.issubset(room_names)


def test_load_people_reads_known_people_without_face_data() -> None:
    people = load_people(CONFIG_DIR / "people.yaml")

    assert people.people[0].name == "Daniela"
    assert people.people[0].relationship == "household member"
    assert people.people[0].recognition == "text-only profile, no face recognition"


def test_load_people_reports_missing_relationship_with_path(tmp_path) -> None:
    path = tmp_path / "people.yaml"
    path.write_text(
        """
people:
  daniela:
    display_name: Daniela
""",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=r"Invalid people config in .*people\.yaml: missing relationship for daniela",
    ):
        load_people(path)
