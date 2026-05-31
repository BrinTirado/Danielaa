from typer.testing import CliRunner

from mochi.cli.main import app
from mochi.memory.store import MemoryStore

runner = CliRunner()


def test_v01_chat_acceptance_flow() -> None:
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["chat"],
            input=(
                "where are you?\n"
                "go to kitchen\n"
                "remember that I like quiet mode after work\n"
                "memories\n"
                "privacy mode on\n"
                "go to bedroom\n"
                "exit\n"
            ),
            env={"MOCHI_MEMORY_PATH": "memory.sqlite3"},
        )

    assert result.exit_code == 0
    assert "living_room" in result.stdout
    assert "kitchen" in result.stdout
    assert "Noted" in result.stdout
    assert "quiet mode after work" in result.stdout
    assert "Privacy mode enabled" in result.stdout
    assert "no-go zone" in result.stdout


def test_v01_chat_memories_do_not_reveal_known_person_memories(tmp_path) -> None:
    memory_path = tmp_path / "memory.sqlite3"
    MemoryStore(memory_path).add_memory(
        person_id="daniela",
        content="Daniela likes quiet mornings.",
        importance=3,
    )

    result = runner.invoke(
        app,
        ["chat"],
        input="memories\nexit\n",
        env={"MOCHI_MEMORY_PATH": str(memory_path)},
    )

    assert result.exit_code == 0
    assert "Daniela likes quiet mornings." not in result.stdout
