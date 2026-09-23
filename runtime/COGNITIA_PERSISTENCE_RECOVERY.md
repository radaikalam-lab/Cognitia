# Cognitia File Persistence P1 — Recovery & Integrity Specification

**Document Version:** 1.0.0  
**Phase:** Persistence P1  

---

## 1. State Recovery Workflow

Upon startup or container recreation, the `RecoveryEngine` executes the following deterministic recovery sequence:

```text
Runtime Startup
      │
      ▼
Check Persistence Configuration & Data Directory
      │
      ▼
Load `metadata.json` (or derive from files)
      │
      ▼
Load `state.json` Snapshot (if present)
      │
      ├── Validate Snapshot Schema Version ("1.0.0")
      │
      ▼
Read & Validate `journal.jsonl`
      │
      ├── Verify Sequence Monotonicity (1, 2, 3, ...)
      ├── Verify SHA-256 Hash Chain Integrity
      └── Detect & Repair Truncated Final Record (if ungraceful crash occurred)
      │
      ▼
Replay Records with Sequence > Snapshot Sequence
      │
      ▼
Reconstruct `InMemoryEpistemicService` Nodes, Evidence & Provenance Store
      │
      ▼
Set Status to HEALTHY & Accept Inbound HTTP Traffic
```

---

## 2. Truncated Tail Repair

When an ungraceful process termination occurs during a write:
1. The journal reader detects an incomplete JSON string on the final line.
2. Middle records are verified for 100% integrity.
3. `repair_truncated_tail()` rewrites the journal containing only validated records.
4. Working state recovers cleanly to the last fully committed record.

---

## 3. Idempotent Replay

Replaying identical journal records produces strictly identical in-memory node structures, confidence scores, and provenance linkages.
