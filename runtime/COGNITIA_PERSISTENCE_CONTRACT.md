# Cognitia File Persistence P1 — Storage Contract Specification

**Document Version:** 1.0.0  
**Interface:** `PersistenceProvider`  
**Phase:** Persistence P1  

---

## 1. Provider Protocol Definition

The persistence subsystem defines a narrow, backend-agnostic storage protocol:

```python
class PersistenceProvider(Protocol):
    def append_record(self, record_type: str, record_id: str, payload: dict[str, Any]) -> JournalRecord:
        """Persist one canonical immutable journal record with sequential hash-chaining."""
        ...

    def create_snapshot(self, state: dict[str, Any], sequence: int | None = None) -> SnapshotData:
        """Atomically persist a consistent snapshot of recoverable working state."""
        ...

    def initialize_and_recover(self) -> tuple[SnapshotData | None, list[JournalRecord]]:
        """Reconstruct working state from snapshot + post-snapshot journal records."""
        ...

    def get_health(self) -> dict[str, Any]:
        """Return logical health status, durability mode, and sequence metrics."""
        ...

    def flush(self) -> None:
        """Flush pending buffers to disk."""
        ...

    def close(self) -> None:
        """Safely flush and close underlying file handles."""
        ...
```

---

## 2. Durability Modes

| Mode | Semantics | Guarantee |
|---|---|---|
| **`sync`** | `write()` $	o$ `flush()` $	o$ `os.fsync()` | Survives OS crash / power cut |
| **`async`** | `write()` $	o$ `flush()` | Survives process termination |
| **`none`** | In-memory synthetic journaling | Ephemeral testing / dev only |

---

## 3. Failure Behavior & Rejection Semantics

- **No Silent Fallback:** If persistent storage is unavailable, unwritable, or corrupted, the runtime enters `PersistenceStatus.FAILED`.
- **Rejection Policy:** Ingestions throw `PersistenceWriteError`, returning `503 Service Unavailable` with error type `PersistenceFailure`.
- Volatile memory updates are strictly aborted on disk write failures.
