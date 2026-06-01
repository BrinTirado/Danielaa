from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class MochiBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class PersonalityConfig(MochiBaseModel):
    vibe: str
    energy_level: str
    humor_style: str
    talkativeness: str


class RobotProfile(MochiBaseModel):
    name: str
    personality: PersonalityConfig
    rules: list[str] = Field(default_factory=list)
    catchphrases: list[str] = Field(default_factory=list)


class MapPosition(MochiBaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)


class Room(MochiBaseModel):
    display_name: str = ""
    description: str = ""
    connected_to: list[str] = Field(default_factory=list)
    map_position: MapPosition | None = None


class HouseMap(MochiBaseModel):
    default_location: str
    rooms: dict[str, Room]
    no_go_zones: list[str] = Field(default_factory=list)


class PersonProfile(MochiBaseModel):
    display_name: str
    relationship: str
    greeting_style: str = ""
    notes: list[str] = Field(default_factory=list)


class PeopleConfig(MochiBaseModel):
    people: dict[str, PersonProfile] = Field(default_factory=dict)


ActionType = Literal[
    "speak",
    "move",
    "dock",
    "remember",
    "forget",
    "privacy_on",
    "privacy_off",
    "set_mood",
]


class ActionCommand(BaseModel):
    type: ActionType | str
    payload: dict[str, Any] = Field(default_factory=dict)


class ActionResult(BaseModel):
    succeeded: bool
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
