from mochi.core.models import HouseMap, Room
from mochi.core.state import RobotState
from mochi.map_console.history import MovementHistory
from mochi.map_console.models import MapSnapshot, RoomSnapshot


def build_map_snapshot(
    *,
    house_map: HouseMap,
    state: RobotState,
    history: MovementHistory,
) -> MapSnapshot:
    return MapSnapshot(
        robot_name=state.name,
        current_location=state.location,
        battery_percent=state.battery_percent,
        mood=state.mood,
        privacy_mode=state.privacy_mode,
        rooms=[
            _room_snapshot(room_id, room, index, house_map.no_go_zones)
            for index, (room_id, room) in enumerate(house_map.rooms.items())
        ],
        no_go_zones=house_map.no_go_zones,
        last_turn=history.last_turn,
        movements=history.movements,
    )


def _room_snapshot(
    room_id: str,
    room: Room,
    index: int,
    no_go_zones: list[str],
) -> RoomSnapshot:
    x, y = _room_position(room, index)
    return RoomSnapshot(
        id=room_id,
        display_name=room.display_name or room_id,
        description=room.description,
        connected_to=room.connected_to,
        no_go_zone=room_id in no_go_zones,
        x=x,
        y=y,
    )


def _room_position(room: Room, index: int) -> tuple[int, int]:
    if room.map_position is not None:
        return room.map_position.x, room.map_position.y
    return 140 + (index % 3) * 220, 120 + (index // 3) * 160
