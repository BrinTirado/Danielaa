import json
import threading
from http.client import HTTPConnection

from mochi.actions.action_router import ActionRouter
from mochi.conversation.engine import ConversationEngine
from mochi.conversation.fake_llm import FakeLLM
from mochi.core.models import (
    HouseMap,
    MapPosition,
    PeopleConfig,
    PersonalityConfig,
    RobotProfile,
    Room,
)
from mochi.core.state import RobotState
from mochi.map_console.runtime import MapConsoleRuntime
from mochi.map_console.server import create_server
from mochi.memory.store import MemoryStore
from mochi.navigation.fake_navigator import FakeNavigator
from mochi.personality.prompt_builder import PersonalityPromptBuilder


def make_runtime(tmp_path) -> MapConsoleRuntime:
    house_map = HouseMap(
        default_location="living_room",
        rooms={
            "living_room": Room(
                display_name="Living Room",
                connected_to=["kitchen", "charging_corner"],
                map_position=MapPosition(x=140, y=150),
            ),
            "kitchen": Room(
                display_name="Kitchen",
                connected_to=["living_room"],
                map_position=MapPosition(x=360, y=150),
            ),
            "charging_corner": Room(
                display_name="Charging Corner",
                connected_to=["living_room"],
                map_position=MapPosition(x=140, y=310),
            ),
        },
        no_go_zones=["bedroom"],
    )
    profile = RobotProfile(
        name="Mochi",
        personality=PersonalityConfig(
            vibe="playful",
            energy_level="medium",
            humor_style="dry",
            talkativeness="low",
        ),
        rules=[],
        catchphrases=[],
    )
    state = RobotState(name="Mochi", location="living_room")
    store = MemoryStore(tmp_path / "memory.sqlite3")
    router = ActionRouter(
        state=state,
        memory_store=store,
        navigator=FakeNavigator(house_map, state),
    )
    conversation = ConversationEngine(
        state=state,
        memory_store=store,
        action_router=router,
        prompt_builder=PersonalityPromptBuilder(profile),
        llm=FakeLLM(response="Tiny robot brain engaged."),
        people=PeopleConfig(),
    )
    return MapConsoleRuntime(
        house_map=house_map,
        state=state,
        conversation_engine=conversation,
    )


def request_json(
    port: int,
    method: str,
    path: str,
    payload: dict | None = None,
) -> tuple[int, dict]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    connection = HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        raw = response.read().decode("utf-8")
        return response.status, json.loads(raw)
    finally:
        connection.close()


def request_text(port: int, method: str, path: str) -> tuple[int, str]:
    connection = HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(method, path)
        response = connection.getresponse()
        raw = response.read().decode("utf-8")
        return response.status, raw
    finally:
        connection.close()


def stop_server(server, thread: threading.Thread) -> None:
    server.shutdown()
    server.server_close()
    thread.join(timeout=1)


def test_server_serves_map_console_html(tmp_path) -> None:
    runtime = make_runtime(tmp_path)
    server = create_server(runtime, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, html = request_text(server.server_port, "GET", "/")
    finally:
        stop_server(server, thread)

    assert status == 200
    assert "Mochi Map Console" in html


def test_server_html_has_no_go_zones_display_hook(tmp_path) -> None:
    runtime = make_runtime(tmp_path)
    server = create_server(runtime, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, html = request_text(server.server_port, "GET", "/")
    finally:
        stop_server(server, thread)

    assert status == 200
    assert 'id="no-go-zones"' in html
    assert "renderNoGoZones(snapshot.no_go_zones || [])" in html
    assert "function renderNoGoZones(noGoZones)" in html


def test_server_serves_snapshot_json(tmp_path) -> None:
    runtime = make_runtime(tmp_path)
    server = create_server(runtime, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, snapshot = request_json(server.server_port, "GET", "/api/snapshot")
    finally:
        stop_server(server, thread)

    assert status == 200
    assert snapshot["current_location"] == "living_room"


def test_server_command_updates_snapshot_and_movement_history(tmp_path) -> None:
    runtime = make_runtime(tmp_path)
    server = create_server(runtime, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, snapshot = request_json(
            server.server_port,
            "POST",
            "/api/command",
            {"text": "go to kitchen"},
        )
    finally:
        stop_server(server, thread)

    assert status == 200
    assert snapshot["current_location"] == "kitchen"
    assert snapshot["movements"][0]["requested_destination"] == "kitchen"


def test_server_voice_turn_rejects_empty_text(tmp_path) -> None:
    runtime = make_runtime(tmp_path)
    server = create_server(runtime, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, payload = request_json(
            server.server_port,
            "POST",
            "/api/voice-turn",
            {"text": " "},
        )
    finally:
        stop_server(server, thread)

    assert status == 400
    assert "cannot be empty" in payload["error"]


def test_server_unknown_post_returns_not_found_before_reading_json(tmp_path) -> None:
    runtime = make_runtime(tmp_path)
    server = create_server(runtime, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
    try:
        connection.request(
            "POST",
            "/api/not-real",
            body=b"{",
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        status = response.status
        payload = json.loads(response.read().decode("utf-8"))
    finally:
        connection.close()
        stop_server(server, thread)

    assert status == 404
    assert payload == {"error": "Not found."}
