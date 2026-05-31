from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError
from yaml import YAMLError

from mochi.core.models import HouseMap, PeopleConfig, RobotProfile


class ConfigError(ValueError):
    pass


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
    except (OSError, YAMLError) as error:
        raise ConfigError(f"Invalid config in {path}: {error}") from error

    if not isinstance(data, dict):
        raise ConfigError(f"Invalid config in {path}: expected YAML mapping")

    return data


def _validate_config(path: Path, model_type: type[RobotProfile | HouseMap | PeopleConfig]):
    try:
        return model_type.model_validate(_load_yaml_mapping(path))
    except (ValidationError, YAMLError, TypeError, ValueError) as error:
        if isinstance(error, ConfigError):
            raise
        raise ConfigError(f"Invalid config in {path}: {error}") from error


def load_robot_profile(path: Path) -> RobotProfile:
    return _validate_config(path, RobotProfile)


def load_house_map(path: Path) -> HouseMap:
    return _validate_config(path, HouseMap)


def load_people_config(path: Path) -> PeopleConfig:
    return _validate_config(path, PeopleConfig)
