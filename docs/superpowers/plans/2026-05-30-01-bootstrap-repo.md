# Bootstrap Repo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create or reconcile the initial Python project skeleton for Mochi Robot Brain v0.1.

**Architecture:** The package should use a `src/mochi` layout with the public CLI at `mochi.cli.main`. Keep early code thin: CLI entrypoint, package metadata, config files, README, and test/lint wiring.

**Tech Stack:** Python 3.11+, Typer, Rich, Pydantic, PyYAML, pytest, ruff.

---

### Task 1: Project Skeleton

**Files:**
- Create or modify: `pyproject.toml`
- Create or modify: `.env.example`
- Create or modify: `.gitignore`
- Create or modify: `README.md`
- Create or modify: `config/robot_profile.yaml`
- Create or modify: `config/house_map.yaml`
- Create or modify: `config/people.yaml`
- Create or modify: `src/mochi/__init__.py`
- Create or modify: `src/mochi/__main__.py`
- Create: `src/mochi/cli/__init__.py`
- Create: `src/mochi/cli/main.py`
- Modify or remove after migration: `src/mochi/cli.py`
- Test: `tests/test_cli.py`

- [x] **Step 1: Write the CLI test**

```python
from typer.testing import CliRunner

from mochi.cli.main import app


runner = CliRunner()


def test_help_lists_chat_command() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Mochi Robot Brain" in result.stdout
    assert "chat" in result.stdout


def test_chat_prints_placeholder_message() -> None:
    result = runner.invoke(app, ["chat"])
    assert result.exit_code == 0
    assert "Mochi v0.1" in result.stdout
    assert "text-only robot brain" in result.stdout
```

- [x] **Step 2: Run the CLI test and confirm it fails before CLI code exists or before imports are updated**

Run: `pytest tests/test_cli.py -v`

Expected: failure from missing `mochi.cli.main`, missing command, or incorrect output.

- [x] **Step 3: Configure packaging**

Ensure `pyproject.toml` includes:

```toml
[project]
name = "mochi-robot-brain"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["pydantic>=2.7", "PyYAML>=6.0.1", "rich>=13.7", "typer>=0.12"]

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.5"]

[project.scripts]
mochi = "mochi.cli.main:main"
```

- [x] **Step 4: Implement the minimal CLI**

`src/mochi/cli/main.py` should expose `app` and `main`:

```python
import typer
from rich.console import Console

console = Console()
app = typer.Typer(help="Mochi Robot Brain v0.1 - a text-only software robot brain.", no_args_is_help=True)


@app.callback()
def root() -> None:
    """Mochi Robot Brain v0.1."""


@app.command()
def chat() -> None:
    """Start a placeholder text-only chat session."""
    console.print("[bold cyan]Mochi v0.1[/bold cyan]: text-only robot brain placeholder.")


def main() -> None:
    app()
```

- [x] **Step 5: Update module entrypoint**

`src/mochi/__main__.py` should be:

```python
from mochi.cli.main import main


if __name__ == "__main__":
    main()
```

- [x] **Step 6: Run verification**

Run: `pytest tests/test_cli.py -v`

Expected: `2 passed`.

Run: `pytest`

Expected: all tests pass.

Run: `ruff check .`

Expected: all checks pass.
