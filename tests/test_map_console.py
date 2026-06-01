from mochi.conversation.engine import ConversationResponse
from mochi.core.models import ActionResult, HouseMap, MapPosition, Room
from mochi.core.state import RobotState
from mochi.map_console.history import MovementHistory
from mochi.map_console.snapshot import build_map_snapshot


def make_map() -> HouseMap:
    return HouseMap(
        default_location="living_room",
        rooms={
            "living_room": Room(
                display_name="Living Room",
                connected_to=["kitchen", "charging_corner"],
            ),
            "kitchen": Room(display_name="Kitchen", connected_to=["living_room"]),
            "charging_corner": Room(
                display_name="Charging Corner",
                connected_to=["living_room"],
            ),
        },
        no_go_zones=["bedroom"],
    )


def test_history_records_successful_move() -> None:
    history = MovementHistory()
    response = ConversationResponse(
        text="Mochi fake-navigated to kitchen.",
        actions=[
            ActionResult(
                succeeded=True,
                message="Mochi fake-navigated to kitchen.",
                payload={"room": "kitchen", "destination": "kitchen"},
            )
        ],
    )

    history.record_turn(
        source="map-ui",
        input_text="go to kitchen",
        response=response,
        start_location="living_room",
        end_location="kitchen",
    )

    assert history.last_turn is not None
    assert history.last_turn.input_text == "go to kitchen"
    assert history.movements[0].requested_destination == "kitchen"
    assert history.movements[0].start_location == "living_room"
    assert history.movements[0].end_location == "kitchen"
    assert history.movements[0].succeeded is True


def test_history_records_blocked_move_without_location_change() -> None:
    history = MovementHistory()
    response = ConversationResponse(
        text="bedroom is a no-go zone.",
        actions=[
            ActionResult(
                succeeded=False,
                message="bedroom is a no-go zone.",
                payload={"room": "bedroom", "destination": "bedroom"},
            )
        ],
    )

    history.record_turn(
        source="map-ui",
        input_text="go to bedroom",
        response=response,
        start_location="living_room",
        end_location="living_room",
    )

    event = history.movements[0]
    assert event.requested_destination == "bedroom"
    assert event.end_location == "living_room"
    assert event.succeeded is False
    assert "no-go zone" in event.message


def test_non_movement_turn_updates_last_turn_only() -> None:
    history = MovementHistory()
    response = ConversationResponse(text="I am in living_room.")

    history.record_turn(
        source="map-ui",
        input_text="where are you?",
        response=response,
        start_location="living_room",
        end_location="living_room",
    )

    assert history.last_turn is not None
    assert history.last_turn.response_text == "I am in living_room."
    assert history.movements == []


def test_history_records_failed_dock_without_destination_payload() -> None:
    history = MovementHistory()
    response = ConversationResponse(
        text="No dock, charging_corner, or charging_station is available.",
        actions=[
            ActionResult(
                succeeded=False,
                message="No dock, charging_corner, or charging_station is available.",
                payload={},
            )
        ],
    )

    history.record_turn(
        source="map-ui",
        input_text="go charge",
        response=response,
        start_location="living_room",
        end_location="living_room",
    )

    event = history.movements[0]
    assert event.requested_destination == "dock"
    assert event.start_location == "living_room"
    assert event.end_location == "living_room"
    assert event.succeeded is False
    assert event.message == "No dock, charging_corner, or charging_station is available."


def test_non_navigation_action_with_room_payload_does_not_record_movement() -> None:
    history = MovementHistory()
    response = ConversationResponse(
        text="Memory saved.",
        actions=[
            ActionResult(
                succeeded=True,
                message="Memory saved.",
                payload={"room": "kitchen"},
            )
        ],
    )

    history.record_turn(
        source="map-ui",
        input_text="remember that the kitchen is sunny",
        response=response,
        start_location="living_room",
        end_location="living_room",
    )

    assert history.last_turn is not None
    assert history.movements == []


def test_build_map_snapshot_contains_rooms_state_and_history() -> None:
    history = MovementHistory()
    response = ConversationResponse(
        text="Mochi fake-navigated to kitchen.",
        actions=[
            ActionResult(
                succeeded=True,
                message="Mochi fake-navigated to kitchen.",
                payload={"room": "kitchen", "destination": "kitchen"},
            )
        ],
    )
    history.record_turn(
        source="voice",
        input_text="go to kitchen",
        response=response,
        start_location="living_room",
        end_location="kitchen",
    )
    snapshot = build_map_snapshot(
        house_map=make_map(),
        state=RobotState(name="Mochi", location="kitchen", battery_percent=86),
        history=history,
    )

    assert snapshot.current_location == "kitchen"
    assert snapshot.battery_percent == 86
    assert snapshot.rooms[0].id == "living_room"
    assert snapshot.rooms[0].connected_to == ["kitchen", "charging_corner"]
    assert snapshot.no_go_zones == ["bedroom"]
    assert snapshot.movements[0].source == "voice"


def test_build_map_snapshot_uses_explicit_positions_and_dumps_json() -> None:
    history = MovementHistory()
    house_map = HouseMap(
        default_location="living_room",
        rooms={
            "living_room": Room(
                display_name="Living Room",
                connected_to=["kitchen"],
                map_position=MapPosition(x=25, y=75),
            ),
            "kitchen": Room(
                display_name="Kitchen",
                connected_to=["living_room"],
                map_position=MapPosition(x=250, y=90),
            ),
        },
    )

    snapshot = build_map_snapshot(
        house_map=house_map,
        state=RobotState(name="Mochi", location="living_room"),
        history=history,
    )

    assert [(room.id, room.x, room.y) for room in snapshot.rooms] == [
        ("living_room", 25, 75),
        ("kitchen", 250, 90),
    ]
    assert snapshot.model_dump(mode="json")["rooms"][0]["x"] == 25
