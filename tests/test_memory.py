from mochi.memory import MemoryStore


def test_memory_store_initializes_sqlite_schema(tmp_path) -> None:
    memory_path = tmp_path / "mochi_memory.sqlite3"
    store = MemoryStore(memory_path)

    store.initialize()
    store.add_memory(kind="session_note", content="Mochi is running in text-only mode.")

    memories = store.list_memories()
    assert len(memories) == 1
    assert memories[0].person_id == "session_note"
    assert memories[0].content == "Mochi is running in text-only mode."
