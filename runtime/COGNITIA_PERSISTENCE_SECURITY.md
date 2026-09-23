# Cognitia File Persistence P1 — Security & Boundary Invariants

**Document Version:** 1.0.0  
**Security Level:** Local-First Least-Privilege  
**Phase:** Persistence P1  

---

## 1. Threat Mitigations

1. **Information Leakage:**
   - Persistence files inherit the strict gateway security boundary. Passwords, authorization tokens, session cookies, and raw secrets are sanitized before ingestion and never recorded on disk.
2. **Path Traversal Attacks:**
   - Storage paths are strictly fixed within the configured `data_dir` (`/var/lib/cognitia/epistemic`). Provider IDs and entity IDs are never used as raw filesystem paths.
3. **Tamper & Corruption Detection:**
   - SHA-256 hash chaining detects any unauthorized modification, deletion, or reordering of journal records.
4. **Command Execution Defense:**
   - Advisory directional proposals recorded on disk remain inert data records with `AUTHORITY = NONE`.

---

## 2. Container Isolation Invariants

- **Read-Only Root Filesystem:** The Docker container runs with `read_only: true`.
- **Designated Mount:** Only `/var/lib/cognitia` is mounted as a writable volume.
- **Unprivileged Execution:** Runs strictly under non-root user `cognitia` (UID 10001, GID 10001).
- **Capability Dropping:** `cap_drop: ALL`, `no-new-privileges: true`.
