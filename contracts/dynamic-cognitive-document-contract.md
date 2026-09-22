# Contract: Dynamic Cognitive Document Contract

**Contract Status**: Authoritative  
**Contract Version**: 1.0.0  
**Phase**: Phase 9 Dynamic Cognitive Documents

---

## 1. Purpose

The **Dynamic Cognitive Document Contract** establishes a provider-neutral, deterministic, auditable projection layer above existing Cognitia structured state. Dynamic Cognitive Documents allow humans to inspect, navigate, contextualize, and express changes to cognitive/domain state without making the document itself the source of truth or an authority mechanism.

---

## 2. Core Invariant

> **A Dynamic Cognitive Document is a human-facing projection of structured state, never the source of truth, never epistemic authority, and never execution authority.**

```text
Structured Cognitia State
        ↓
Dynamic Document Projection
        ↓
Human
```

---

## 3. Document Is Projection

A Dynamic Cognitive Document is a deterministic transformation of canonical Cognitia state. It is not durable storage, not memory, not persistence, not epistemic authority, and not domain authority.

Explicitly:

```text
Document ≠ Source of Truth
Document ≠ Memory
Document ≠ Persistence
Document ≠ Epistemic Authority
Document ≠ Domain Authority
Document ≠ Execution Command
```

---

## 4. Document Model

### 4.1 DynamicDocument

```text
DynamicDocument
  ├── document_id: UUID
  ├── schema_version: SemVer
  ├── document_version: str
  ├── title: str
  ├── document_type: str
  ├── source_references: tuple[DocumentReference, ...]
  ├── sections: tuple[DocumentSection, ...]
  ├── metadata: dict[str, Any]
  ├── created_at: ISO-8601 UTC timestamp
  ├── updated_at: ISO-8601 UTC timestamp
  └── provenance: ProvenanceRecord
```

A `DynamicDocument` is a `CognitiveObject` subclass. It carries immutable identity, versioning, and provenance.

### 4.2 DocumentSection

```text
DocumentSection
  ├── section_id: UUID
  ├── section_type: SectionType (TEXT, TABLE, TIMELINE, GRAPH, METRICS, OBSERVATIONS, EVIDENCE, HYPOTHESES, CLAIMS, REASONING, DECISIONS, DIRECTION, CONFLICTS, PROVENANCE, RESIDUALS)
  ├── title: str
  ├── content: tuple[SectionContent, ...]
  ├── ordering: tuple[str, ...] | None
  ├── filters: dict[str, Any] | None
  ├── provenance: ProvenanceRecord
  └── metadata: dict[str, Any]
```

A section describes **what is being projected**, not how a browser renders it.

### 4.3 SectionContent

```text
SectionContent
  ├── content_id: UUID
  ├── content_type: str
  ├── reference: DocumentReference | None
  ├── text: str | None
  ├── data: tuple[tuple[str, Any], ...] | None
  └── metadata: dict[str, Any]
```

### 4.4 DocumentReference

```text
DocumentReference
  ├── reference_id: UUID
  ├── artifact_id: UUID
  ├── artifact_type: str
  ├── schema_version: str
  ├── source_node_id: str | None
  ├── origin_node_id: str | None
  └── metadata: dict[str, Any]
```

A `DocumentReference` preserves canonical artifact identity. It does not create a second identity system.

### 4.5 DocumentVersion

```text
DocumentVersion
  ├── version_id: UUID
  ├── document_id: UUID
  ├── document_version: str
  ├── specification_hash: str
  ├── state_hash: str
  ├── created_at: ISO-8601 UTC timestamp
  └── provenance: ProvenanceRecord
```

---

## 5. Structured References

Documents reference canonical Cognitia artifacts rather than copying them as independent truth.

Referencable artifacts include:

```text
Observation
Evidence
Experience
Hypothesis
Claim
ReasoningTrace
Decision
DirectionalSpecification
DirectionalProposal
CognitiveConflict
ProvenanceRecord
MemoryContext
RecallResult
```

A document reference preserves:

```text
artifact_id
artifact_type
schema_version
source/provenance information where applicable
```

Canonical artifact identity remains authoritative.

---

## 6. Projection Semantics

A projection transforms canonical Cognitia state into a `DynamicDocument`.

Projection must be:

* **deterministic**: identical source + identical specification → identical document
* **read-only** with respect to source state
* **reproducible**
* **provenance-aware**
* **versioned**
* **explainable**

For identical canonical source state and identical projection specification:

```text
Projection(A) == Projection(A)
```

The resulting document must not depend on:

* current wall-clock time
* random UUID generation
* network state
* provider availability
* iteration-order accidents
* mutable global state

unless such information is explicitly part of the source state.

---

## 7. Document Specification

A `DocumentSpecification` describes what the document should project.

```text
DocumentSpecification
  ├── specification_id: UUID
  ├── document_type: str
  ├── title: str
  ├── requested_artifacts: tuple[DocumentReference, ...] | None
  ├── requested_sections: tuple[SectionSpecification, ...] | None
  ├── filters: dict[str, Any] | None
  ├── ordering: tuple[str, ...] | None
  ├── context_scope: dict[str, Any] | None
  ├── attention_scope: dict[str, Any] | None
  ├── provenance_visibility: bool
  ├── epistemic_visibility: bool
  ├── conflict_visibility: bool
  ├── residual_visibility: bool
  ├── provenance: ProvenanceRecord
  └── metadata: dict[str, Any]
```

### 7.1 SectionSpecification

```text
SectionSpecification
  ├── section_type: SectionType
  ├── title: str
  ├── artifact_types: tuple[str, ...] | None
  ├── filters: dict[str, Any] | None
  ├── ordering: tuple[str, ...] | None
  └── metadata: dict[str, Any]
```

A specification describes **what should be represented**, not how to compute it. It aligns with the Directional Programming architecture: declarative intent, not imperative script.

---

## 8. Dynamic Document ≠ Directional Specification

Preserve the distinction.

A document may **contain or project**:

```text
DirectionalSpecification
DirectionalProposal
```

but:

```text
DynamicDocument ≠ DirectionalSpecification
```

and:

```text
DirectionalProposal ≠ DocumentCommand
```

A human editing a directional section must ultimately produce a structured `DirectionalSpecification` or other canonical artifact, not mutate hidden document state.

---

## 9. Human Edits / Intent Capture

A `DocumentIntent` represents human-requested document changes.

```text
DocumentIntent
  ├── intent_id: UUID
  ├── document_id: UUID
  ├── intent_type: IntentType (ADD_REFERENCE, REMOVE_REFERENCE, CHANGE_SECTION, CHANGE_FILTER, CHANGE_ORDER, UPDATE_DIRECTION, ANNOTATE, REQUEST_REFRESH, REQUEST_PROJECTION)
  ├── parameters: tuple[tuple[str, Any], ...]
  ├── rationale: str | None
  ├── provenance: ProvenanceRecord
  └── metadata: dict[str, Any]
```

Important:

```text
Document Intent
      ↓
Validation / Translation
      ↓
Canonical Cognitia Artifact or Specification
```

Never:

```text
Document Edit
      ↓
Direct Mutation
      ↓
Authority
```

---

## 10. No Hidden State

A Dynamic Cognitive Document must not contain undocumented semantic state.

Every meaningful value should be traceable to:

* a canonical artifact
* a projection specification
* a deterministic transformation
* explicit human input

A document must not silently invent:

* observations
* claims
* evidence
* causal relationships
* confidence
* epistemic status
* decisions
* domain state

---

## 11. Epistemic Preservation

Dynamic documents preserve existing epistemic semantics without promotion.

For example:

```text
UNKNOWN
OBSERVED
HYPOTHESIS
TESTABLE
SUPPORTED
REFUTED
UNRESOLVED
```

A document projection must not convert:

```text
HYPOTHESIS → FACT
```

or:

```text
UNKNOWN → FALSE
```

or:

```text
UNRESOLVED → RESOLVED
```

Likewise:

```text
Decision confidence
```

must not be presented as:

```text
scientific certainty
```

unless the underlying source explicitly establishes that meaning.

---

## 12. Contradictions and Conflicts

Documents preserve contradictions.

If source state contains conflicting claims or evidence, the document must not silently select one.

Likewise for distributed conflicts:

```text
CognitiveConflict
```

must remain visible.

Do not introduce:

```text
latest wins
central wins
highest confidence wins
majority wins
```

as implicit document behavior.

---

## 13. Provenance

Every generated document must have provenance.

The provenance chain should make it possible to establish:

```text
Document
   ↓
Projection Specification
   ↓
Source Artifacts
   ↓
Underlying Provenance
```

The document must not create a competing provenance model. Use the existing `ProvenanceRecord` and existing provenance semantics. If the projection itself is deterministic, record that fact.

---

## 14. Versioning

Documents are versioned representations.

Preserve:

```text
document_id
document_version
schema_version
```

A changed projection should produce a new document version or deterministic regenerated representation according to the chosen contract. Do not mutate historical document versions destructively. Historical versions must remain reconstructable where persistence is available.

---

## 15. Persistence Integration

Integrate with existing Cognitia persistence. Do not create a second persistence system.

The document layer may persist:

```text
DynamicDocument
DocumentSpecification
DocumentIntent
DocumentVersion
Projection metadata
```

using the existing persistence abstractions.

Remember:

```text
Persistence = durable history
Document = projection
```

Authoritative contract: `contracts/persistence-contract.md`.

---

## 16. Memory / Recall Integration

Documents may consume:

```text
MemoryContext
RecallResult
```

but must not redefine them.

The boundary remains:

```text
Persistence
    ↓
Memory
    ↓
Recall
    ↓
Document Projection
```

A document may show why an artifact was recalled or selected, but it must not silently alter recall semantics.

Authoritative contracts: `contracts/memory-contract.md`, `contracts/recall-contract.md`.

---

## 17. Context / Attention Integration

Allow document specifications to request:

```text
Context scope
Attention scope
```

but preserve their existing semantics.

The document should be capable of expressing:

> "Show me the observations and reasoning relevant to this question."

without creating a new context or attention engine.

Authoritative contracts: `contracts/context-contract.md`, `contracts/attention-contract.md`.

---

## 18. Reasoning Integration

A document may project:

```text
ReasoningTrace
ReasoningResult
Residuals
Hypotheses
Counterfactuals
Causal hypotheses
```

but must not reinterpret them.

For example:

```text
CausalHypothesis
```

must remain a hypothesis. A document cannot promote it into:

```text
Established causal fact
```

merely because it appears in a document section.

Authoritative contract: `contracts/reasoning-contract.md`.

---

## 19. Directional Programming Integration

A Dynamic Cognitive Document should be capable of projecting:

```text
Current State
Desired Direction
Objectives
Constraints
Success Criteria
Residuals
Candidate Proposals
```

using the existing Directional Programming structures.

But:

```text
Proposal ≠ Action
Proposal ≠ Execution
Proposal ≠ Authority
```

Authoritative contract: `contracts/directional-programming-contract.md`.

---

## 20. Distributed Cognition Integration

Documents remain valid across Cognitia nodes.

Preserve:

```text
origin_node_id
processing_node_id
artifact_id
provenance
document identity
```

Do not create:

```text
EdgeDocument
CentralDocument
```

as separate semantic types.

Distributed arrival order must not silently become document truth ordering.

Authoritative contract: `contracts/distributed-cognition-contract.md`.

---

## 21. Document Refresh

Refresh is a deterministic mechanism:

```text
DocumentSpecification
        +
Current Canonical State
        ↓
Refresh
        ↓
New Document Version
```

Refresh must not mutate source artifacts. A refresh should be reproducible from:

```text
specification
source state
projection implementation/version
```

---

## 22. Document Diff / Change Explanation

A `DocumentChange` explains structural changes between document versions:

```text
DocumentChange
  ├── change_id: UUID
  ├── document_id: UUID
  ├── from_version: str
  ├── to_version: str
  ├── changes: tuple[ChangeEntry, ...]
  └── provenance: ProvenanceRecord

ChangeEntry
  ├── change_type: ChangeType (ADDED, REMOVED, CHANGED, UNCHANGED)
  ├── path: str
  ├── old_value: Any | None
  ├── new_value: Any | None
  └── metadata: dict[str, Any]
```

This must not become an epistemic judgment. For example:

```text
Observation X changed
```

is valid.

But:

```text
Observation X became more true
```

is not a document-level inference.

---

## 23. Dynamic Document Capability

The document subsystem integrates with the existing capability architecture:

```text
CapabilityType
  ├── ...
  └── DYNAMIC_DOCUMENT
```

A `DynamicDocumentProvider` follows the existing:

```text
Capability
Provider
Gateway
Provenance
```

architecture. No separate capability registry is introduced.

---

## 24. Deterministic Default Provider

The initial implementation is structural and deterministic. No:

* LLM
* embedding model
* vector database
* network
* browser
* AI framework
* external service

The deterministic default provider proves that Cognitia can transform structured state into a human-facing dynamic document representation without introducing semantic authority.

---

## 25. Authority Boundary

```text
Dynamic Document ≠ Authority
Document Projection ≠ Domain Validation
Document Projection ≠ Safety Validation
Document Projection ≠ Execution
Document Intent ≠ Command
Directional Proposal ≠ Action
```

Cognitia remains advisory. Domain applications remain authoritative over:

* physical execution
* safety
* business transactions
* scientific experimental execution
* actuator control
* real-time constraints

Authoritative contract: `contracts/authority-boundary.md`.

---

## 26. Zero Dependencies

Phase 9 maintains:
- 0 external runtime dependencies
- 0 network dependencies
- 0 AI/ML frameworks

---

## 27. Integration Points

- **Cognitive ABI**: All document types follow canonical ABI identity, versioning, timestamp, and serialization rules. Authoritative contract: `contracts/cognitive-abi.md`.
- **Persistence**: Documents persist via existing `PersistenceStore`. Authoritative contract: `contracts/persistence-contract.md`.
- **Provenance**: Documents use existing `ProvenanceRecord`. Authoritative contract: `contracts/provenance-contract.md`.
- **Capability**: Document capability integrates with existing `CapabilityRegistry` and `ProviderGateway`. Authoritative contract: `contracts/capability-contract.md`.
- **Model Registry**: Documents may reference model versions via existing registry. Authoritative contract: `contracts/model-registry-contract.md`.
- **Reasoning**: Documents project existing `ReasoningTrace` without reinterpretation. Authoritative contract: `contracts/reasoning-contract.md`.
- **Epistemic**: Documents preserve existing epistemic states. Authoritative contract: `contracts/epistemic-contract.md`.
- **Directional Programming**: Documents project existing directional structures. Authoritative contract: `contracts/directional-programming-contract.md`.
- **Distributed Cognition**: Documents preserve node identity and provenance across nodes. Authoritative contract: `contracts/distributed-cognition-contract.md`.
- **Memory/Recall**: Documents consume existing `MemoryContext` and `RecallResult`. Authoritative contracts: `contracts/memory-contract.md`, `contracts/recall-contract.md`.
- **Authority Boundary**: Documents introduce no new authority. Authoritative contract: `contracts/authority-boundary.md`.
