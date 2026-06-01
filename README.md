# Mochi Robot Brain

Mochi is a software-first robot brain for a future home robot. The project is
building the decision, conversation, memory, personality, and adapter seams
first, so the software can grow toward physical robotics later without coupling
the conversation system directly to hardware.

## Current Phase

v0.2 is software-only. It includes the v0.1 text brain plus:

- Fake voice input and output seams.
- A simulated voice command path through the conversation engine.
- A local browser map console for fake navigation state.
- Movement history for successful and blocked fake moves.

v0.2 does not include real robot hardware, ROS, cameras, microphones, motors,
live audio capture, real speaker output, webcam awareness, autonomous background
loops, or Home Assistant.

## Requirements

- Python 3.11+

## Install

Create a virtual environment and install Mochi in editable mode with developer
dependencies:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

If `python3` points to Python 3.11 or newer on your machine, this also works:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Run

Start a local text-only chat session:

```bash
mochi chat
```

Show Mochi's fake robot state:

```bash
mochi state
```

List explicitly saved local memories:

```bash
mochi memories
```

Delete one memory by id:

```bash
mochi forget <memory-id>
```

Turn privacy mode on or off for the current local session:

```bash
mochi privacy on
mochi privacy off
```

Run one fake voice turn:

```bash
mochi voice "go to kitchen"
```

Start the local map console:

```bash
mochi map-ui
```

## Chat Commands

Inside `mochi chat`, v0.1 supports a small text command surface:

- `where are you?` shows the current fake location.
- `go to kitchen` asks the fake navigator to move.
- `go to bedroom` demonstrates a configured no-go zone.
- `remember that I like quiet mode after work` saves an explicit memory.
- `memories` lists saved memories during the chat session.
- `privacy mode on` and `privacy mode off` toggle privacy mode.
- `exit` or `quit` ends chat.

## Test

Run the test suite:

```bash
pytest
```

Run lint checks:

```bash
ruff check .
```

Format code when needed:

```bash
ruff format .
```

## Configuration

Mochi reads YAML config from `config/` by default. Set `MOCHI_CONFIG_DIR` to
point at another config directory.

- `config/robot_profile.yaml` defines Mochi's name, personality, behavior
  rules, and catchphrases.
- `config/house_map.yaml` defines the fake home map, the default location,
  connected rooms, and no-go zones.
- `config/people.yaml` defines known people for prompt context. Unknown people
  are not enrolled or remembered automatically.

Local memory defaults to `data/mochi_memory.sqlite3`. Set `MOCHI_MEMORY_PATH`
to use another SQLite file, which is useful for tests or disposable runs.

## Privacy Rules

- Mochi stores private information only when explicitly asked with a remember
  command.
- Memories can be listed with `mochi memories` or the `memories` chat command.
- Individual memories can be deleted with `mochi forget <memory-id>`.
- Privacy mode suppresses proactive speech and behavior suggestions.
- Unknown people are not enrolled or remembered automatically.

## Project Layout

```text
config/                 YAML configuration for the fake robot brain
src/mochi/              Python package
tests/                  pytest test suite
docs/                   Plans, lessons, and project notes
```

## Roadmap

- v0.2: Fake voice seams and local map console.
- v0.3: Voice input/output provider experiment.
- v0.4: Webcam awareness.
- v0.5: Autonomous loop.
- v0.6: Home Assistant integration.
- v0.7: ROS/Gazebo simulation.
- v1.0: Real hardware adapter.
