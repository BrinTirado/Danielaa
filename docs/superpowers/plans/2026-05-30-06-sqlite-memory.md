# SQLite Memory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement explicit, SQLite-backed local memory for Mochi v0.1.

**Architecture:** Memories live in `src/mochi/memory/store.py` behind `MemoryStore`. The conversation system must call memory methods only for explicit remember/forget commands, never for every conversation turn.

**Tech Stack:** sqlite3, Pydantic, pytest, ruff.

---

### Task 1: Memory Model and Store

**Files:**
- Create or modify: `src/mochi/memory/__init__.py`
- Create: `src/mochi/memory/models.py`
- Create or modify: `src/mochi/memory/store.py`
- Test: `tests/test_memory_store.py`

- [x] **Step 1: Write tests**

```python
from mochi.memory.store import MemoryStore


def test_memory_persists_across_store_instances(tmp_path) -> None:
    db_path = tmp_path / "memory.sqlite3"
    first = MemoryStore(db_path)
    memory = first.add_memory(person_id="daniela", content="likes quiet mode", importance=3)

    second = MemoryStore(db_path)
    memories = second.list_memories()

    assert memories[0].id == memory.id
    assert memories[0].content == "likes quiet mode"


def test_memory_search_and_delete(tmp_path) -> None:
    store = MemoryStore(tmp_path / "memory.sqlite3")
    keep = store.add_memory(person_id="daniela", content="likes tea", importance=2)
    delete = store.add_memory(person_id="roommate", content="prefers quiet", importance=1)

    assert [memory.id for memory in store.search_memories(text="tea")] == [keep.id]
    assert [memory.id for memory in store.search_memories(person_id="roommate")] == [delete.id]

    assert store.delete_memory(delete.id) is True
    assert [memory.id for memory in store.list_memories()] == [keep.id]


def test_delete_all_for_person(tmp_path) -> None:
    store = MemoryStore(tmp_path / "memory.sqlite3")
    store.add_memory(person_id="daniela", content="one", importance=1)
    store.add_memory(person_id="daniela", content="two", importance=1)
    store.add_memory(person_id="roommate", content="three", importance=1)

    assert store.delete_memories_for_person("daniela") == 2
    assert len(store.list_memories()) == 1
```

- [x] **Step 2: Run tests to verify red**

Run: `pytest tests/test_memory_store.py -v`

Expected: failure for missing model fields or search/delete methods.

- [x] **Step 3: Implement `Memory` model**

Fields:

```python
id: str
person_id: str | None
content: str
importance: int = Field(ge=1, le=5)
created_at: datetime
```

- [x] **Step 4: Implement SQLite schema**

Use table `memories(id TEXT PRIMARY KEY, person_id TEXT, content TEXT NOT NULL, importance INTEGER NOT NULL, created_at TEXT NOT NULL)`.

- [x] **Step 5: Implement store methods**

Methods:

```python
add_memory(person_id: str | None, content: str, importance: int = 1) -> Memory
list_memories() -> list[Memory]
search_memories(person_id: str | None = None, text: str | None = None) -> list[Memory]
delete_memory(memory_id: str) -> bool
delete_memories_for_person(person_id: str) -> int
```

- [x] **Step 6: Run verification**

Run: `pytest tests/test_memory_store.py -v`

Expected: all tests pass.

Run: `pytest && ruff check .`

Expected: all tests and lint checks pass.
