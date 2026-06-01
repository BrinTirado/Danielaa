import os
from dataclasses import dataclass
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from mochi.actions.action_router import ActionRouter
from mochi.conversation.engine import ConversationEngine
from mochi.conversation.fake_llm import FakeLLM
from mochi.core.models import ActionCommand, HouseMap, PeopleConfig, RobotProfile
from mochi.core.settings import load_house_map, load_people_config, load_robot_profile
from mochi.core.state import RobotState
from mochi.map_console.runtime import MapConsoleRuntime
from mochi.map_console.server import create_server
from mochi.memory.store import MemoryStore
from mochi.navigation.fake_navigator import FakeNavigator
from mochi.personality.prompt_builder import PersonalityPromptBuilder
from mochi.voice.engine import VoiceEngine
from mochi.voice.fake import FakeSpeechRecognizer, FakeSpeechSynthesizer

console = Console(width=140)

app = typer.Typer(
    help="Mochi Robot Brain v0.1 - a text-only software robot brain.",
    no_args_is_help=True,
)


@dataclass(frozen=True)
class Runtime:
    robot_profile: RobotProfile
    house_map: HouseMap
    people: PeopleConfig
    state: RobotState
    memory_store: MemoryStore
    navigator: FakeNavigator
    action_router: ActionRouter
    prompt_builder: PersonalityPromptBuilder
    llm: FakeLLM
    engine: ConversationEngine


def build_runtime() -> Runtime:
    """Build Mochi's local text-only runtime with fake hardware adapters."""
    repo_root = Path(__file__).resolve().parents[3]
    config_dir = Path(os.environ.get("MOCHI_CONFIG_DIR", repo_root / "config")).expanduser()
    memory_path = Path(
        os.environ.get("MOCHI_MEMORY_PATH", "data/mochi_memory.sqlite3")
    ).expanduser()

    robot_profile = load_robot_profile(config_dir / "robot_profile.yaml")
    house_map = load_house_map(config_dir / "house_map.yaml")
    people = load_people_config(config_dir / "people.yaml")

    state = RobotState.from_config(robot_profile, house_map)
    memory_store = MemoryStore(memory_path)
    navigator = FakeNavigator(house_map, state)
    action_router = ActionRouter(
        state=state,
        memory_store=memory_store,
        navigator=navigator,
    )
    prompt_builder = PersonalityPromptBuilder(robot_profile)
    llm = FakeLLM()
    engine = ConversationEngine(
        state=state,
        memory_store=memory_store,
        action_router=action_router,
        prompt_builder=prompt_builder,
        llm=llm,
        people=people,
    )

    return Runtime(
        robot_profile=robot_profile,
        house_map=house_map,
        people=people,
        state=state,
        memory_store=memory_store,
        navigator=navigator,
        action_router=action_router,
        prompt_builder=prompt_builder,
        llm=llm,
        engine=engine,
    )


@app.callback()
def root() -> None:
    """Mochi Robot Brain v0.1."""


@app.command()
def chat() -> None:
    """Start a local text-only chat session."""
    runtime = build_runtime()
    console.print("[bold cyan]Mochi v0.1[/bold cyan]: text-only robot brain.")

    while True:
        try:
            user_input = console.input("[bold green]You[/bold green]: ")
        except EOFError:
            console.print()
            break

        message = user_input.strip()
        if not message:
            continue
        if message.lower() in {"exit", "quit"}:
            break

        response = runtime.engine.respond(message)
        console.print(f"[bold cyan]Mochi[/bold cyan]: {response.text}")


@app.command()
def voice(message: str) -> None:
    """Run one fake voice turn through Mochi."""
    runtime = build_runtime()
    synthesizer = FakeSpeechSynthesizer()
    voice_engine = VoiceEngine(
        conversation_engine=runtime.engine,
        recognizer=FakeSpeechRecognizer([message]),
        synthesizer=synthesizer,
    )

    try:
        result = voice_engine.handle_turn()
    except ValueError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=2) from error

    table = Table(title="Mochi Fake Voice Turn")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value")
    table.add_row("Recognized", result.input.text)
    table.add_row("Response", result.response_text)
    table.add_row("Spoken", result.output.text)
    if result.actions:
        action_summary = ", ".join(
            "succeeded" if action.succeeded else "failed" for action in result.actions
        )
        table.add_row("Actions", action_summary)
    console.print(table)


@app.command("map-ui")
def map_ui(
    host: str = "127.0.0.1",
    port: int = 8765,
    dry_run: bool = False,
) -> None:
    """Start the local Mochi map console."""
    runtime = build_runtime()
    console_runtime = MapConsoleRuntime(
        house_map=runtime.house_map,
        state=runtime.state,
        conversation_engine=runtime.engine,
    )
    url = f"http://{host}:{port}"
    console.print(f"Mochi map console: {url}")
    if dry_run:
        return

    try:
        server = create_server(console_runtime, host=host, port=port)
    except OSError as error:
        console.print(f"[red]Could not start map console on {url}: {error}[/red]")
        raise typer.Exit(code=1) from error

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        console.print()
    finally:
        server.server_close()


@app.command()
def state() -> None:
    """Show Mochi's fake robot state."""
    robot_state = build_runtime().state
    table = Table(title="Mochi State")
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    table.add_row("name", robot_state.name)
    table.add_row("location", robot_state.location)
    table.add_row("battery", f"{robot_state.battery_percent}%")
    table.add_row("mood", robot_state.mood)
    table.add_row("privacy mode", "enabled" if robot_state.privacy_mode else "disabled")
    console.print(table)


@app.command()
def memories() -> None:
    """List explicitly saved local memories."""
    stored_memories = build_runtime().memory_store.list_memories()
    table = Table(title="Mochi Memories")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Person ID", no_wrap=True)
    table.add_column("Content", no_wrap=True)
    table.add_column("Importance", justify="right", no_wrap=True)

    for memory in stored_memories:
        table.add_row(
            memory.id,
            memory.person_id or "",
            memory.content,
            str(memory.importance),
        )

    console.print(table)


@app.command()
def forget(memory_id: str) -> None:
    """Delete one memory by id."""
    runtime = build_runtime()
    result = runtime.action_router.execute(
        ActionCommand(type="forget", payload={"memory_id": memory_id})
    )
    console.print(result.message)
    if not result.succeeded:
        raise typer.Exit(code=1)


@app.command()
def privacy(mode: str) -> None:
    """Turn privacy mode on or off for this local session."""
    normalized_mode = mode.lower()
    if normalized_mode not in {"on", "off"}:
        console.print("[red]Privacy mode must be 'on' or 'off'.[/red]")
        raise typer.Exit(code=2)

    command_type = "privacy_on" if normalized_mode == "on" else "privacy_off"
    result = build_runtime().action_router.execute(ActionCommand(type=command_type))
    if result.succeeded:
        status = "enabled" if normalized_mode == "on" else "disabled"
        console.print(f"Privacy mode {status}.")
    else:
        console.print(result.message)
    if not result.succeeded:
        raise typer.Exit(code=1)


def main() -> None:
    app()
