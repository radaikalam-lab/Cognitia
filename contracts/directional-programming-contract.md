# Contract: Directional Programming Contract

**Contract Status**: Authoritative  
**Contract Version**: 1.0.0  
**Phase**: Phase 7 Directional Programming

---

## 1. Purpose

The **Directional Programming Contract** introduces a provider-neutral paradigm for specifying desired cognitive outcomes (what to achieve) independent of execution mechanisms (how to achieve them). It defines immutable directional specifications, candidate proposals, explicit residuals, and governed lifecycle states.

---

## 2. Core Invariants

1. **Specification vs. Execution Separation**:
   A `DirectionalSpecification` declares desired outcomes, objectives, constraints, and success criteria. It contains no execution logic, actuator bindings, or hardware control directives.

2. **Advisory Proposals Only**:
   A `DirectionalProposal` is a candidate solution emitted by a provider. It is advisory and does not constitute physical truth, decision authority, or execution permission.

3. **Explicit Residuals**:
   Every proposal MUST report residuals explaining why it cannot fully satisfy the specification. Residuals are first-class cognitive objects with provenance.

4. **Authority Boundary**:
   Cognitia proposes; the consuming domain application/authority decides and executes. Directional Programming introduces no execution authority.

5. **Provider Neutrality**:
   Directional specifications and proposals are provider-agnostic. Any registered provider implementing the `DirectionalProvider` protocol can evaluate a specification.

6. **Deterministic Baseline**:
   A deterministic baseline provider is provided. No mandatory external AI/ML/network dependencies are introduced.

---

## 3. Directional Concepts & Schemas

### 3.1 DirectionalObjective
```text
DirectionalObjective
  ├── id: UUID
  ├── description: str
  ├── target_state: dict[str, Any]
  ├── priority: float ([0.0, 1.0])
  └── metrics: list[str]
```

### 3.2 DirectionalConstraint
```text
DirectionalConstraint
  ├── id: UUID
  ├── description: str
  ├── constraint_type: str (hard, soft)
  ├── bound: dict[str, Any]
  └── is_hard: bool
```

### 3.3 SuccessCriterion
```text
SuccessCriterion
  ├── id: UUID
  ├── description: str
  ├── metric_name: str
  ├── threshold: float
  └── direction: str (>=, <=, ==)
```

### 3.4 DirectionalSpecification
```text
DirectionalSpecification
  ├── id: UUID
  ├── schema_version: SemVer
  ├── created_at: ISO-8601 UTC timestamp
  ├── objectives: tuple[DirectionalObjective, ...]
  ├── constraints: tuple[DirectionalConstraint, ...]
  ├── success_criteria: tuple[SuccessCriterion, ...]
  ├── provenance: ProvenanceRecord
  └── metadata: dict[str, Any]
```

### 3.5 DirectionalResidual
```text
DirectionalResidual
  ├── id: UUID
  ├── factor_name: str
  ├── description: str
  ├── residual_type: str (TARGET_UNDEFINED, CONSTRAINT_VIOLATED, CONFLICTING_OBJECTIVES, RESOURCE_UNAVAILABLE, KNOWLEDGE_GAP, AMBIGUOUS_CRITERIA)
  ├── target_variable: str | None
  └── provenance: ProvenanceRecord
```

### 3.6 DirectionalProposal
```text
DirectionalProposal
  ├── id: UUID
  ├── schema_version: SemVer
  ├── created_at: ISO-8601 UTC timestamp
  ├── specification_id: str
  ├── provider_id: str
  ├── provider_version: str
  ├── proposed_actions: tuple[tuple[str, Any], ...]
  ├── residuals: tuple[DirectionalResidual, ...]
  ├── confidence: float ([0.0, 1.0])
  ├── proposal_status: ProposalLifecycleStatus
  ├── epistemic_status: EpistemicStatus
  ├── provenance: ProvenanceRecord
  └── metadata: dict[str, Any]
```

---

## 4. Directional Service Interface (SPI)

```python
class DirectionalService(Protocol):
    def create_specification(
        self,
        objectives: Sequence[DirectionalObjective],
        constraints: Sequence[DirectionalConstraint] = (),
        success_criteria: Sequence[SuccessCriterion] = (),
        metadata: Mapping[str, Any] | None = None,
    ) -> DirectionalSpecification: ...

    def get_specification(self, specification_id: str) -> DirectionalSpecification | None: ...

    def list_specifications(self) -> list[DirectionalSpecification]: ...

    def propose(
        self,
        specification_id: str,
        provider_id: str,
        provider_version: str = "1.0.0",
    ) -> DirectionalProposal: ...

    def get_proposal(self, proposal_id: str) -> DirectionalProposal | None: ...

    def list_proposals(self, specification_id: str | None = None) -> list[DirectionalProposal]: ...
```

---

## 5. Directional Provider Interface (SPI)

```python
class DirectionalProvider(Protocol):
    provider_id: str
    provider_version: str

    def propose(
        self,
        specification: DirectionalSpecification,
    ) -> DirectionalProposal: ...
```

---

## 6. Lifecycle & Governance

### 6.1 Proposal Lifecycle
Proposals follow the canonical `ProposalLifecycleStatus`:
`PROPOSED` → `VALIDATED` → `APPROVED` → `ACTIVATABLE` → `ACTIVATED` → `RETIRED`

Rejected proposals transition to `REJECTED`.

### 6.2 Epistemic Status
New proposals start with `EpistemicStatus.UNRESOLVED`. Epistemic evaluation is an explicit downstream step.

### 6.3 Authority Boundary
The directional service and providers operate strictly within the Cognitive Plane. They do not:
- Execute actions
- Mutate production state
- Bind to hardware actuators
- Assume domain authority

---

## 7. Integration Points

- **Persistence**: Specifications and proposals are `CognitiveObject` subclasses and persist via `PersistenceStore`.
- **Provenance**: All directional objects carry immutable `ProvenanceRecord` lineage.
- **Provider Registry**: Directional providers register via `AdvancedProviderRegistry` with `AdvancedCapabilityType.DIRECTIONAL_PROGRAMMING`.
- **Gateway**: Provider execution is authorized via `ProviderGateway`.
- **Epistemic Service**: Proposal epistemic state transitions are managed by `EpistemicService`.
