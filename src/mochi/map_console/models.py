from pydantic import Field

from mochi.core.models import ActionResult, MochiBaseModel


class ConsoleTurn(MochiBaseModel):
    source: str
    input_text: str
    response_text: str
    actions: list[ActionResult] = Field(default_factory=list)


class MovementEvent(MochiBaseModel):
    id: int
    source: str
    command: str
    requested_destination: str
    start_location: str
    end_location: str
    succeeded: bool
    message: str


class RoomSnapshot(MochiBaseModel):
    id: str
    display_name: str
    description: str
    connected_to: list[str] = Field(default_factory=list)
    no_go_zone: bool = False
    x: int
    y: int


class MapSnapshot(MochiBaseModel):
    robot_name: str
    current_location: str
    battery_percent: int
    mood: str
    privacy_mode: bool
    rooms: list[RoomSnapshot] = Field(default_factory=list)
    no_go_zones: list[str] = Field(default_factory=list)
    last_turn: ConsoleTurn | None = None
    movements: list[MovementEvent] = Field(default_factory=list)
