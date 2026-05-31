from pathlib import Path
from typing import Any

import yaml

from mochi.models import HouseMap, PeopleConfig, RobotProfile


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping in {path}")

    return data


def load_robot_profile(path: Path) -> RobotProfile:
    data = _load_yaml_mapping(path)
    if "version" not in data:
        data["version"] = "0.1"
    if "capabilities" not in data:
        data["capabilities"] = {}
    personality = data.get("personality")
    if isinstance(personality, dict) and "tone" not in personality:
        data["personality"] = {
            "tone": "warm, curious, and gently playful",
            "traits": [personality["vibe"]] if "vibe" in personality else [],
            "response_style": personality.get("talkativeness", "concise, kind, and grounded"),
        }
    return RobotProfile.model_validate(data)


def load_house_map(path: Path) -> HouseMap:
    data = _load_yaml_mapping(path)
    if "default_location" in data:
        data["home_name"] = data.get("home_name", "Mochi House")
        data["start_location"] = data.get("start_location", data["default_location"])
    rooms = data.get("rooms")
    if isinstance(rooms, dict):
        data["rooms"] = [{"name": name, **room} for name, room in rooms.items()]
    return HouseMap.model_validate(data)


def load_people(path: Path) -> PeopleConfig:
    data = _load_yaml_mapping(path)
    people = data.get("people")
    if isinstance(people, dict):
        legacy_people = []
        for key, person in people.items():
            if "relationship" not in person:
                raise ValueError(f"Invalid people config in {path}: missing relationship for {key}")
            legacy_people.append(
                {
                    "name": person.get("display_name", key),
                    "relationship": person["relationship"],
                    "recognition": "text-only profile, no face recognition",
                    "notes": person.get("notes", []),
                }
            )
        data["people"] = legacy_people
    return PeopleConfig.model_validate(data)
