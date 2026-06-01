import json
import threading
from http.client import HTTPConnection
from pathlib import Path
from typing import Any

from pytest import MonkeyPatch
from typer.testing import CliRunner

from mochi.cli.main import app, build_runtime
from mochi.map_console.runtime import MapConsoleRuntime
from mochi.map_console.server import create_server

runner = CliRunner()


def test_v02_voice_acceptance_flow() -> None:
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["voice", "go to kitchen"],
            env={"MOCHI_MEMORY_PATH": "memory.sqlite3"},
        )

    assert result.exit_code == 0
    assert "Recognized" in result.stdout
    assert "go to kitchen" in result.stdout
    assert "Spoken" in result.stdout
    assert "kitchen" in result.stdout
    assert "Actions" in result.stdout
    assert "succeeded" in result.stdout


def test_v02_map_console_acceptance_flow(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("MOCHI_MEMORY_PATH", str(tmp_path / "memory.sqlite3"))
    runtime = build_runtime()
    console_runtime = MapConsoleRuntime(
        house_map=runtime.house_map,
        state=runtime.state,
        conversation_engine=runtime.engine,
    )
    server = create_server(console_runtime, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        status, snapshot = post_json(
            server.server_port,
            "/api/command",
            {"text": "go to kitchen"},
        )
        blocked_status, blocked_snapshot = post_json(
            server.server_port,
            "/api/command",
            {"text": "go to bedroom"},
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)

    assert not thread.is_alive()
    assert status == 200
    assert snapshot["current_location"] == "kitchen"
    assert blocked_status == 200
    assert blocked_snapshot["current_location"] == "kitchen"
    assert blocked_snapshot["movements"][-1]["requested_destination"] == "bedroom"
    assert blocked_snapshot["movements"][-1]["succeeded"] is False


def post_json(port: int, path: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    connection = HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(
            "POST",
            path,
            body=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        body = json.loads(response.read().decode("utf-8"))
        return response.status, body
    finally:
        connection.close()
