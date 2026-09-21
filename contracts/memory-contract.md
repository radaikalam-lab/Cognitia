# Contract: Cognitive Memory, Plasticity & Consolidation Contract

**Contract Status**: Authoritative  
**Contract Version**: 1.0.0  
**Phase**: Phase 0 Foundation  

---

## 1. Purpose & Core Principles

The **Cognitive Memory, Plasticity & Consolidation Contract** establishes the architectural framework for turning accumulated operational experience into controlled cognitive adaptation over time.

### Fundamental Invariants
> **Persistence provides longitudinal continuity; plasticity operators propose candidate adaptations; epistemics evaluates what should be supported; consolidation promotes validated patterns into versioned structures.**
>
> $$\text{Persistence} \neq \text{Memory} \neq \text{Learning} \neq \text{Consolidation} \neq \text{Authority}$$

* **Persistence**: Preserves immutable historical artifacts, traces, and events (*What happened?*).
* **Memory**: Structured retrieval selecting relevant cognitive context (*What is relevant now?*).
* **Learning (Plasticity)**: Processing experience via Plasticity Operators into candidate proposals (*What patterns might exist?*).
* **Consolidation**: Controlled promotion of validated candidates into versioned structures ($N \rightarrow N+1$) (*What has proven stable enough to retain?*).
* **Authority**: Sovereign domain control (*What actions/truth are authorized?*).

---

## 2. Plasticity-Inspired Cognitive Adaptation Loop

```text
                 EXPERIENCE
                      │
                      ▼
                 PERSISTENCE
                      │
                      ▼
                MEMORY RETRIEVAL
                      │
                      ▼
         PLASTICITY OPERATOR (Laya / TinyML / Rules)
                      │
                      ▼
          CANDIDATE LEARNING ARTIFACT
                      │
                      ▼
             EPISTEMIC EVALUATION
                      │
               ┌──────┴──────┐
               │             │
            REFUTED      SUPPORTED
               │             │
               ▼             ▼
          Historical   CONSOLIDATION
            Record           │
                             ▼
                      VALIDATION GATE
                             │
                             ▼
                    VERSION N+1 CREATED
                             │
                             ▼
                      MODEL REGISTRY
```

### Critical Rules
1. **No Automatic Runtime Self-Modification**: Candidate learning artifacts are proposals for adaptation, never direct or unvalidated mutations of active production model weights.
2. **Versioned Evolution**: Consolidation creates a new version ($N+1$) in the Model Registry. Version $N$ remains historically immutable and queryable.
3. **Forgetting as Deprioritization**: Forgetting is modeled as supersession, attenuation, or status retirement (`DEPRECATED`, `RETIRED`), never physical destruction of historical provenance.

---

## 3. Cognitive Memory SPI

Cognitive Memory operates strictly as a structured, read-oriented query layer over the Persistence Plane.

```python
class MemoryStore(Protocol):
    """Protocol for provider-agnostic cognitive memory retrieval."""

    def retrieve(self, query: MemoryQuery) -> list[CognitiveObject]:
        """Retrieve relevant persisted cognitive objects matching query criteria."""
        ...

    def get_context(self, query: MemoryQuery) -> MemoryContext:
        """Assemble structured memory context retaining original entity identities and provenance."""
        ...
```

### 3.1 MemoryQuery Schema
```text
MemoryQuery
 ├── agent_id: Optional[str]
 ├── environment_id: Optional[str]
 ├── episode_id: Optional[str]
 ├── source_application: Optional[str]
 ├── time_range: Optional[tuple[str, str]] (ISO-8601 UTC start/end)
 ├── object_types: Optional[list[str]] (e.g., ["observation", "experience", "hypothesis"])
 ├── epistemic_status: Optional[EpistemicStatus]
 ├── model_version: Optional[str]
 ├── limit: Optional[int]
 └── metadata_filters: dict[str, Any]
```

### 3.2 MemoryContext Schema
```text
MemoryContext
 ├── id: UUID
 ├── schema_version: SemVer
 ├── created_at: ISO-8601 UTC timestamp
 ├── query: MemoryQuery
 ├── experiences: list[ExperienceRecord]
 ├── observations: list[Observation]
 ├── evidence: list[Evidence]
 ├── hypotheses: list[Hypothesis]
 ├── claims: list[Claim]
 ├── reasoning_traces: list[ReasoningTrace]
 ├── decisions: list[Decision]
 ├── outcomes: list[Outcome]
 ├── epistemic_states: dict[str, EpistemicStatus]
 ├── provenance: ProvenanceRecord
 └── metadata: dict[str, Any]
```

---

## 4. Plasticity Operators & Candidate Learning Artifacts

### 4.1 CandidateLearningArtifact Schema
```text
CandidateLearningArtifact
 ├── id: UUID
 ├── schema_version: SemVer
 ├── created_at: ISO-8601 UTC timestamp
 ├── candidate_type: CandidateType (PATTERN, ASSOCIATION, PREDICTION, HYPOTHESIS, RULE_CANDIDATE, MODEL_REVISION, REPRESENTATION_REVISION)
 ├── source_memory_ids: list[str] (References to MemoryContext / Experience IDs)
 ├── proposed_change: dict[str, Any] (Structured adaptation specification)
 ├── rationale: str
 ├── confidence: float ([0.0, 1.0] Plasticity operator proposal confidence)
 ├── provider: str (e.g., "tiny_ml_detector", "laya", "rule_miner")
 ├── model_version: Optional[str]
 └── provenance: ProvenanceRecord
```

---

## 5. Consolidation Service Interface

```python
class ConsolidationService(Protocol):
    """Protocol for evaluating and consolidating candidate learning artifacts."""

    def evaluate_candidate(
        self,
        candidate: CandidateLearningArtifact,
        epistemic_service: EpistemicService,
    ) -> ConsolidationResult:
        """Evaluate a learning candidate against epistemic criteria."""
        ...

    def consolidate(
        self,
        result: ConsolidationResult,
        model_registry: ModelRegistry,
    ) -> ModelRecord | None:
        """Promote a supported consolidation result to a new ModelRecord (Version N+1)."""
        ...
```

### 5.1 ConsolidationResult Schema
```text
ConsolidationResult
 ├── id: UUID
 ├── schema_version: SemVer
 ├── created_at: ISO-8601 UTC timestamp
 ├── candidate_id: str
 ├── status: ConsolidationStatus (PENDING, SUPPORTED, REFUTED, CONSOLIDATED, REJECTED)
 ├── epistemic_justification: str
 ├── target_model_id: str
 ├── proposed_version: str (e.g., "1.1.0")
 ├── calibration_checksum: str
 └── provenance: ProvenanceRecord
```

---

## 6. Biological Metaphor & Collective Cognition Note

The biological analogies used throughout Cognitia (plasticity, memory consolidation, hive-like distributed worker coordination) are **architectural design metaphors only**, not claims of biological equivalence. Formal contracts adhere strictly to computational, epistemic, and deterministic SPI abstractions.
