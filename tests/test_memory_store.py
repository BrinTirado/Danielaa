import pytest
from pydantic import ValidationError

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


def test_rejects_empty_or_blank_content(tmp_path) -> None:
    store = MemoryStore(tmp_path / "memory.sqlite3")

    with pytest.raises(ValueError):
        store.add_memory(person_id="daniela", content="")

    with pytest.raises(ValueError):
        store.add_memory(person_id="daniela", content="   ")


def test_invalid_importance_raises_validation_error(tmp_path) -> None:
    store = MemoryStore(tmp_path / "memory.sqlite3")

    with pytest.raises(ValidationError):
        store.add_memory(person_id="daniela", content="likes tea", importance=6)


def test_delete_missing_or_already_deleted_memory_returns_false(tmp_path) -> None:
    store = MemoryStore(tmp_path / "memory.sqlite3")
    memory = store.add_memory(person_id="daniela", content="likes tea", importance=2)

    assert store.delete_memory("missing-id") is False
    assert store.delete_memory(memory.id) is True
    assert store.delete_memory(memory.id) is False


def test_search_treats_like_wildcards_as_literal_text(tmp_path) -> None:
    store = MemoryStore(tmp_path / "memory.sqlite3")
    literal = store.add_memory(person_id="daniela", content="battery is 100% ready", importance=1)
    store.add_memory(person_id="daniela", content="battery is 100x ready", importance=1)

    assert [memory.id for memory in store.search_memories(text="100%")] == [literal.id]
