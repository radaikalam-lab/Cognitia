# Contract: Epistemic Contract

**Contract Status**: Authoritative  
**Contract Version**: 1.0.0  
**Phase**: Phase 0 Foundation  

---

## 1. Purpose

The **Epistemic Contract** establishes epistemics as a first-class, domain-neutral service inside the Cognitive Plane. It formalizes knowledge representation, multi-observation evidence tracking, hypothesis formation, challenges, residuals, and non-linear versioned transitions.

---

## 2. Core Epistemic Invariants

1. **Epistemic Independence**:
   The Epistemic Service MUST operate deterministically and fully independently of AI, ML, LLMs, neural networks, or external cloud services.
2. **Non-Equivalence to Physical Truth**:
   $$\text{Epistemic State} \neq \text{Physical Reality}$$
   An epistemic claim represents an internal state of belief/support based on current evidence; it never constitutes authoritative physical fact.
3. **Non-Linear State Transitions**:
   Epistemic lifecycles are non-linear. Competing hypotheses, challenges, revisions, and branching inquiries are first-class concepts.

---

## 3. Epistemic Concepts & Schemas

### 3.1 EpistemicStatus (Active State)
* `UNKNOWN`: Unassessed or uncharacterized phenomenon.
* `OBSERVED`: Empirical phenomena recorded without formal hypothesis.
* `HYPOTHESIS`: Formulated testable proposition.
* `TESTABLE`: Proposition equipped with explicit test criteria.
* `SUPPORTED`: Proposition corroborated by supporting evidence.
* `REFUTED`: Proposition contradicted/falsified by counter-evidence.
* `UNRESOLVED`: Conflicting or inconclusive evidence encountered.

### 3.2 TransitionOutcome (Governance Lifecycle — Phase 2)
* `REVISION_PROPOSED`: Modification of hypothesis or model requested.
* `ACCEPTED`: Proposal approved into the active cognitive model.
* `REJECTED`: Proposal dismissed.
*(Note: Transition outcomes govern offline model evolution and candidate approval pipelines; Phase 0 runtime state transitions operate over `EpistemicStatus`)*.

### 3.3 Evidence Schema (COG-003 Resolved)
```text
Evidence
 ├── id: UUID
 ├── schema_version: SemVer
 ├── created_at: ISO-8601 UTC timestamp
 ├── target_id: str (Target Hypothesis, Claim, or Model ID)
 ├── observation: Optional[Observation] (Primary direct observation, if single)
 ├── observation_ids: list[str] (List of upstream observation IDs for multi-sensor/batch evidence)
 ├── direction: EvidenceDirection (SUPPORT, REFUTE, NEUTRAL)
 ├── confidence: float ([0.0, 1.0] Evidential reliability/corroboration strength)
 ├── weight: float (Relative weight in multi-evidence evaluation)
 └── provenance: ProvenanceRecord (Lineage including all parent observation IDs)
```

### 3.4 Claim Schema
```text
Claim
 ├── id: UUID
 ├── schema_version: SemVer
 ├── created_at: ISO-8601 UTC timestamp
 ├── statement: str
 ├── confidence: float ([0.0, 1.0] Degree of epistemic belief based on evidence)
 ├── status: EpistemicStatus
 └── provenance: ProvenanceRecord
```

### 3.5 Challenge & Residual Schemas
* **`Challenge`**: A formal dispute or falsification attempt lodged against an existing Claim, Hypothesis, or Model carrying `counter_evidence_ids`.
* **`Residual`**: The unexplained variance or discrepancy between predicted and observed outcomes.

---

## 4. Epistemic Service Interface (SPI)

```python
class EpistemicService(Protocol):
    def record_observation(self, observation: Observation) -> EpistemicNode: ...
    def register_evidence(self, evidence: Evidence) -> EpistemicNode: ...
    def register_hypothesis(self, hypothesis: Hypothesis) -> EpistemicNode: ...
    def register_claim(self, claim: Claim) -> EpistemicNode: ...
    def issue_challenge(self, challenge: Challenge) -> EpistemicTransition: ...
    def record_residual(self, residual: Residual) -> EpistemicNode: ...
    def transition_state(
        self,
        node_id: str,
        new_status: EpistemicStatus,
        reason: str,
        provenance: ProvenanceRecord | None = None,
    ) -> EpistemicTransition: ...
    def get_node(self, node_id: str) -> EpistemicNode | None: ...
    def get_history(self, node_id: str) -> list[EpistemicTransition]: ...
    def list_nodes_by_status(self, status: EpistemicStatus) -> list[EpistemicNode]: ...
```

---

## 5. Branching & History Preservation
* Epistemic state transitions are append-only.
* Past transitions, reasons, and historical confidence ratings MUST NOT be overwritten or mutated.
