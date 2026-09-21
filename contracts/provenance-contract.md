# Contract: Provenance Contract

**Contract Status**: Authoritative  
**Contract Version**: 1.0.0  
**Phase**: Phase 0 Foundation  

---

## 1. Purpose

The **Provenance Contract** establishes the foundational data integrity, auditability, and lineage tracking standard for every cognitive entity produced within or passed through Cognitia.

---

## 2. Core Invariants

1. **Mandatory Lineage**:
   Every synthesized or derived cognitive artifact (Claim, Decision, Trace, Hypothesis) MUST carry a valid `ProvenanceRecord`.
2. **Immutable History**:
   Provenance records MUST NEVER be overwritten, mutated, or deleted during model upgrades or system recalibrations.
3. **Explicit Determinism**:
   Every provenance record MUST declare whether the producing computation was strictly deterministic (`is_deterministic = True`) or non-deterministic.
4. **Canonical Checksumming**:
   Where applicable, input/artifact checksums MUST be computed over deterministic serialized representations using standard cryptographic hashes (SHA-256).

---

## 3. Provenance Record Schema

```text
ProvenanceRecord
 ├── id: UUID
 ├── schema_version: SemVer
 ├── created_at: ISO-8601 UTC timestamp
 ├── source_type: SourceType (HUMAN, DETERMINISTIC_RULE, ML_MODEL, NEURAL_MODEL, REASONING_ENGINE, SENSOR, COMPOSITE)
 ├── producer_id: str (Identifier of specific agent, capability, or hardware)
 ├── capability_id: Optional[str]
 ├── model_id: Optional[str]
 ├── model_version: Optional[str]
 ├── parent_ids: list[str] (Immediate lineage parents / input references)
 ├── input_checksums: dict[str, str] (SHA-256 hashes of input artifacts)
 ├── artifact_checksum: Optional[str] (SHA-256 hash of output payload)
 ├── is_deterministic: bool
 └── metadata: dict[str, Any]
```

---

## 4. Lineage Chain Traversal

A `LineageChain` provides depth-first and breadth-first audit traversal across parent entity IDs:
$$\text{Lineage}(A) = \{ A \} \cup \bigcup_{p \in \text{parents}(A)} \text{Lineage}(p)$$

No circular references are permitted in the lineage graph (Directed Acyclic Graph invariant).
