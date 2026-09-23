# Cognitia File Persistence P1 — Architecture Specification

**Component:** Durable Epistemic File Persistence  
**Version:** 1.0.0  
**Phase:** Persistence P1  
**Status:** Validated & Frozen  
**Cognitive ABI:** 1.0.0  
**Authority:** NONE  

---

## 1. Architectural Model

The Cognitia File Persistence layer provides durable, deterministic, and auditable storage for the in-memory working state of the Cognitia Epistemic runtime.

```text
                    COGNITIA RUNTIME
                           │
                 Epistemic Bridge
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
      Working Memory            Durable Persistence
  (InMemoryEpistemicService)    (FilePersistenceService)
                                        │
                                        ▼
                               Local File System
                           /var/lib/cognitia/epistemic/
                                ├── metadata.json
                                ├── state.json (Snapshot)
                                └── journal.jsonl (Append-Only)
```

- **Working Memory:** High-speed in-memory indexing, graph traversal, and epistemic query evaluation.
- **Durable File Store:** Monotonically sequenced append-only journal (`journal.jsonl`), atomic snapshots (`state.json`), and database metadata (`metadata.json`).
- **Decoupled Provider Contract:** Strict `PersistenceProvider` interface allowing seamless addition of future backends (e.g. SQLite, PostgreSQL) without altering epistemic semantics.

---

## 2. Ingestion & Write Order Invariant

Durable operations strictly enforce the write-before-memory invariant:

```text
HTTP Ingestion Request (/v1/observations, /v1/evidence, /v1/directional-specifications)
              │
              ▼
   ABI & Payload Security Validation
              │
              ▼
   Build Canonical Entities (Observation / Evidence + ProvenanceRecord)
              │
              ▼
   Persist to Journal (Append + Flush + fsync for Sync Durability)
              │  (On disk write failure -> Raise PersistenceWriteError -> Return 503)
              ▼
   Apply to In-Memory Working State (EpistemicService & ProvenanceStore)
              │
              ▼
   Acknowledge HTTP Request (200 OK)
```

**Key Invariant:** A 200 OK HTTP response guarantees that the entity is durably recorded on disk.

---

## 3. Storage Layout & Format

All persistent data is stored in human-readable, UTF-8 JSON / JSONL format:

1. **`metadata.json`**:
   - `persistence_schema_version`: `"1.0.0"`
   - `runtime_abi_version`: `"1.0.0"`
   - `durable_sequence`: Highest persisted journal sequence number
   - `snapshot_sequence`: Sequence number at which last snapshot was taken
   - `genesis_hash` & `head_hash`: SHA-256 hash chaining roots
   - `total_records`: Lifetime count of recorded entries

2. **`state.json` (Atomic Snapshots)**:
   - Full consolidated working state of all active epistemic nodes, evidence links, provenance records, and advisory directional proposals.
   - Written using temporary files and atomic `os.replace` to prevent partial write corruption.

3. **`journal.jsonl` (Append-Only Hash-Chained Log)**:
   - One JSON record per line.
   - SHA-256 hash chaining: `record_hash = SHA256(canonical_json(schema, sequence, type, id, ts, payload, previous_hash))`.
