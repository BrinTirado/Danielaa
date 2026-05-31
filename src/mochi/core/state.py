from pydantic import ConfigDict, Field

from mochi.core.models import HouseMap, MochiBaseModel, RobotProfile


class RobotState(MochiBaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, validate_assignment=True)

    name: str
    location: str
    battery_percent: int = Field(default=100, ge=0, le=100)
    mood: str = "curious"
    privacy_mode: bool = False
    active_person: str | None = None
    last_action: str | None = None

    def set_location(self, location: str) -> None:
        self.location = location
        self.last_action = f"move:{location}"

    def set_battery_percent(self, percent: int) -> None:
        self.battery_percent = percent
        self.last_action = f"battery:{percent}"

    def set_privacy_mode(self, enabled: bool) -> None:
        self.privacy_mode = enabled
        self.last_action = "privacy:on" if enabled else "privacy:off"

    def set_mood(self, mood: str) -> None:
        self.mood = mood
        self.last_action = f"mood:{mood}"

    def set_active_person(self, person_id: str | None) -> None:
        self.active_person = person_id
        self.last_action = f"person:{person_id or 'none'}"

    @classmethod
    def from_config(cls, robot_profile: RobotProfile, house_map: HouseMap) -> "RobotState":
        return cls(name=robot_profile.name, location=house_map.default_location)
