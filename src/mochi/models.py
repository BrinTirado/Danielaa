from pydantic import BaseModel, Field


class PersonalityConfig(BaseModel):
    tone: str
    traits: list[str] = Field(default_factory=list)
    response_style: str


class CapabilityConfig(BaseModel):
    hardware_enabled: bool = False
    ros_enabled: bool = False
    camera_enabled: bool = False
    microphone_enabled: bool = False
    face_recognition_enabled: bool = False
    home_assistant_enabled: bool = False


class RobotProfile(BaseModel):
    name: str
    version: str
    personality: PersonalityConfig
    capabilities: CapabilityConfig


class Room(BaseModel):
    name: str
    display_name: str
    description: str
    connected_to: list[str] = Field(default_factory=list)


class HouseMap(BaseModel):
    home_name: str
    start_location: str
    rooms: list[Room]


class PersonProfile(BaseModel):
    name: str
    relationship: str
    recognition: str
    notes: list[str] = Field(default_factory=list)


class PeopleConfig(BaseModel):
    people: list[PersonProfile] = Field(default_factory=list)
