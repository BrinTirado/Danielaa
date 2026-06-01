import os
import socket
import subprocess
import sys
from pathlib import Path

from typer.testing import CliRunner

from mochi.cli import main
from mochi.cli.main import app
from mochi.memory.store import MemoryStore

runner = CliRunner()


def invoke_cli(args: list[str], *, input: str | None = None):
    with runner.isolated_filesystem():
        return runner.invoke(
            app,
            args,
            input=input,
            env={"MOCHI_MEMORY_PATH": "memory.sqlite3"},
        )


def test_state_command_shows_location() -> None:
    result = invoke_cli(["state"])
    assert result.exit_code == 0
    assert "name" in result.stdout
    assert "Mochi" in result.stdout
    assert "location" in result.stdout
    assert "living_room" in result.stdout
    assert "battery" in result.stdout
    assert "100%" in result.stdout
    assert "mood" in result.stdout
    assert "curious" in result.stdout
    assert "privacy mode" in result.stdout
    assert "disabled" in result.stdout


def test_privacy_commands_toggle_without_crashing() -> None:
    on = invoke_cli(["privacy", "on"])
    off = invoke_cli(["privacy", "off"])
    assert on.exit_code == 0
    assert "enabled" in on.stdout
    assert off.exit_code == 0
    assert "disabled" in off.stdout


def test_chat_exits_cleanly() -> None:
    result = invoke_cli(["chat"], input="where are you?\nexit\n")
    assert result.exit_code == 0
    assert "living_room" in result.stdout


def test_help_lists_chat_command() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Mochi Robot Brain" in result.stdout
    for command in ("chat", "state", "memories", "forget", "privacy"):
        assert command in result.stdout


def test_help_lists_v02_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in ("voice", "map-ui"):
        assert command in result.stdout


def test_voice_command_runs_fake_voice_turn() -> None:
    result = invoke_cli(["voice", "where are you?"])

    assert result.exit_code == 0
    assert "Recognized" in result.stdout
    assert "where are you?" in result.stdout
    assert "Spoken" in result.stdout
    assert "living_room" in result.stdout


def test_voice_command_moves_fake_robot() -> None:
    result = invoke_cli(["voice", "go to kitchen"])

    assert result.exit_code == 0
    assert "go to kitchen" in result.stdout
    assert "kitchen" in result.stdout
    assert "succeeded" in result.stdout


def test_map_ui_command_prints_url_without_serving_forever() -> None:
    result = invoke_cli(["map-ui", "--dry-run"])

    assert result.exit_code == 0
    assert "http://127.0.0.1:8765" in result.stdout
    assert "Mochi map console" in result.stdout


def test_map_ui_dry_run_prints_custom_url_without_binding() -> None:
    result = invoke_cli(["map-ui", "--host", "localhost", "--port", "9001", "--dry-run"])

    assert result.exit_code == 0
    assert "Mochi map console: http://localhost:9001" in result.stdout


def test_map_ui_command_failure_does_not_print_success_url() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied_socket:
        occupied_socket.bind(("127.0.0.1", 0))
        occupied_socket.listen()
        occupied_port = occupied_socket.getsockname()[1]

        result = invoke_cli(["map-ui", "--port", str(occupied_port)])

    assert result.exit_code == 1
    assert "Could not start map console" in result.stdout
    assert f"http://127.0.0.1:{occupied_port}" in result.stdout
    assert "Mochi map console:" not in result.stdout


def test_map_ui_command_reports_actual_bound_port(monkeypatch) -> None:
    class FakeServer:
        server_port = 54321

        def serve_forever(self) -> None:
            raise KeyboardInterrupt

        def server_close(self) -> None:
            return

    monkeypatch.setattr(
        sys.modules["mochi.cli.main"], "create_server", lambda *args, **kwargs: FakeServer()
    )

    result = invoke_cli(["map-ui", "--port", "0"])

    assert result.exit_code == 0
    assert "Mochi map console: http://127.0.0.1:54321" in result.stdout
    assert "http://127.0.0.1:0" not in result.stdout


def test_memories_command_lists_saved_memory(tmp_path: Path) -> None:
    memory_path = tmp_path / "memory.sqlite3"
    memory = MemoryStore(memory_path).add_memory(
        person_id="daniela",
        content="Daniela likes quiet mornings.",
        importance=3,
    )

    result = runner.invoke(
        app,
        ["memories"],
        env={"MOCHI_MEMORY_PATH": str(memory_path)},
    )

    assert result.exit_code == 0
    assert memory.id in result.stdout
    assert "daniela" in result.stdout
    assert "Daniela likes quiet mornings." in result.stdout
    assert "3" in result.stdout


def test_forget_command_deletes_memory(tmp_path: Path) -> None:
    memory_path = tmp_path / "memory.sqlite3"
    store = MemoryStore(memory_path)
    memory = store.add_memory(
        person_id="daniela",
        content="Delete this after review.",
        importance=2,
    )

    result = runner.invoke(
        app,
        ["forget", memory.id],
        env={"MOCHI_MEMORY_PATH": str(memory_path)},
    )

    assert result.exit_code == 0
    assert store.list_memories() == []


def test_python_module_help_lists_commands(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = {
        **os.environ,
        "MOCHI_MEMORY_PATH": str(tmp_path / "memory.sqlite3"),
        "PYTHONPATH": str(repo_root / "src"),
    }

    result = subprocess.run(
        [sys.executable, "-m", "mochi", "--help"],
        cwd=repo_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    for command in ("chat", "state", "memories", "forget", "privacy"):
        assert command in result.stdout


def test_chat_prints_intro() -> None:
    result = invoke_cli(["chat"], input="exit\n")

    assert result.exit_code == 0
    assert "Mochi v0.1" in result.stdout


def test_legacy_cli_import_exposes_callable_main() -> None:
    assert callable(main)
