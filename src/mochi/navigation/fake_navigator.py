from collections.abc import Iterable

from mochi.core.models import HouseMap, Room
from mochi.core.state import RobotState
from mochi.navigation.base import NavigationResult


class FakeNavigator:
    def __init__(
        self,
        house_map: HouseMap | None = None,
        state: RobotState | None = None,
        *,
        known_locations: Iterable[str] | None = None,
    ) -> None:
        if house_map is None:
            if known_locations is None:
                msg = "FakeNavigator requires a HouseMap or known_locations."
                raise TypeError(msg)
            known_locations = set(known_locations)
            house_map = HouseMap(
                default_location=next(iter(known_locations), "living_room"),
                rooms={location: Room() for location in known_locations},
            )

        self.house_map = house_map
        self.state = state

    def move_to(self, room: str) -> NavigationResult:
        if room in self.house_map.no_go_zones:
            return NavigationResult(
                succeeded=False,
                message=f"{room} is a no-go zone.",
                destination=room,
            )

        if room not in self.house_map.rooms:
            return NavigationResult(
                succeeded=False,
                message=f"Unknown room: {room}.",
                destination=room,
            )

        if self.state is None:
            msg = "FakeNavigator.move_to requires a RobotState."
            raise TypeError(msg)

        self.state.set_location(room)
        return NavigationResult(
            succeeded=True,
            message=f"Mochi fake-navigated to {room}.",
            destination=room,
        )

    def dock(self) -> NavigationResult:
        for destination in ("charging_station", "charging_corner", "dock"):
            if destination in self.house_map.rooms:
                return self.move_to(destination)

        return NavigationResult(
            succeeded=False,
            message="No dock, charging_corner, or charging_station is available.",
        )

    def go_to(self, state: RobotState, destination: str) -> NavigationResult:
        previous_state = self.state
        self.state = state
        result = self.move_to(destination)
        if not result.succeeded:
            self.state = previous_state
        if not result.succeeded and result.message.startswith("Unknown room:"):
            return NavigationResult(
                succeeded=False,
                message=f"Unknown location: {destination}.",
                destination=destination,
            )
        return result
