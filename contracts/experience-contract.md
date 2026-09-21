# Contract: Experience Contract

**Contract Status**: Authoritative  
**Contract Version**: 1.0.0  
**Phase**: Phase 0 Foundation  

---

## 1. Purpose

The **Experience Contract** defines the domain-neutral episodic bridge between consuming applications (e.g., AcoustiForge, CellForge, Swarms, Autonomous Robots) and the Cognitia cognitive services.

---

## 2. Distinction: Observation vs. Evidence vs. Experience

To prevent semantic conflation:

* **Observation**: A single or structured data point captured from a sensor, telemetry stream, or environment node.
* **Evidence**: An observation or collection of observations evaluated specifically to substantiate, refute, or challenge an epistemic proposition (Claim, Hypothesis, Model).
* **Experience**: An episodic encapsulation of context, observations, actions taken, expected outcomes, and actual outcomes resulting from execution.

---

## 3. Experience Record Schema

```text
ExperienceRecord
 ├── id: UUID (Unique experience identifier)
 ├── schema_version: SemVer (e.g., "1.0.0")
 ├── created_at: ISO-8601 UTC timestamp
 ├── source_application: str (e.g., "acoustiforge", "cellforge", "robotics_edge")
 ├── source_node: str (Node / hardware device ID)
 ├── agent_id: str (Agent identifier within the source application)
 ├── environment_id: str (Environment or execution arena ID)
 ├── episode_id: str (Episode or operational cycle ID)
 ├── observation: Observation (Captured initial/contextual observation)
 ├── action: Action (Action or operational directive executed)
 ├── expected_outcome: Outcome (Predicted / anticipated outcome)
 ├── actual_outcome: Outcome (Observed / measured outcome)
 ├── model_version: Optional[str] (Model version used to guide action, if any)
 ├── cognitive_library_version: str (Cognitia library version)
 └── provenance: ProvenanceRecord (Lineage and creation audit trail)
```

---

## 4. Multi-Agent & Swarm Invariants

1. **Topology Neutrality**: The `agent_id`, `source_node`, and `environment_id` fields MUST accommodate single-agent, hierarchical multi-agent, and decentralized swarm deployments.
2. **Immutable Episodes**: Once an experience record is finalized and recorded, its fields MUST be strictly immutable.
3. **No Domain Leakage**: The experience record MUST NOT mandate domain-specific payload types (e.g., acoustics, cellular biology, kinematics); payloads are structured dictionaries adhering to ABI typing.
