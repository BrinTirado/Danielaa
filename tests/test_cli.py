import os
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
