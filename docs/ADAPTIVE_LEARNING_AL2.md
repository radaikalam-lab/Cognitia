# Cognitia Adaptive Learning AL2 — Domain-Scoped Learning, Knowledge Isolation, and Controlled Transfer

## 1. Executive Summary

**Adaptive Learning AL2** builds upon the AL1 outcome-based learning loop by establishing **explicit domain-scoped learning boundaries** and a formal, advisory **knowledge transfer protocol**.

Cognitia enables multi-tenant, multi-application intelligence without allowing unconstrained or implicit sharing between domains:

$$\text{Domain Scope} \implies \text{Isolated Learning Loop} \xrightarrow[\text{Explicit Protocol}]{\text{Advisory Transfer Proposal}} \text{Target Candidate (Advisory Only)}$$

### Core Guarantees:
1. **Domain Isolation**: Every observation, prediction, outcome, feedback record, candidate model, and evaluation is strictly bounded by an explicitly registered `LearningDomain`.
2. **Explicit Transfer**: Knowledge never crosses domain boundaries implicitly or automatically. Cross-domain transfer requires an explicit, provenance-bearing `LearningTransferProposal`.
3. **Advisory Authority (`authority = NONE`)**: All transfer proposals, compatibility assessments, and target candidate models carry `authority = "NONE"`.
4. **Target Active Model Immutability**: Instantiating a transfer candidate generates a `ModelCandidate` in the target domain with `status = CANDIDATE`; it **never modifies, replaces, or activates the target domain's active production model**.
5. **External Decision Provenance**: Transfer decisions are captured in `TransferDecisionRecord` with `decision_source = "EXTERNAL"` and `cognitia_authority = "NONE"`. Cognitia never originates an authoritative activation decision.

---

## 2. Core Architectural Invariants

### 2.1 LearningDomain is Scope, Not Authority
A `LearningDomain` represents a bounded semantic context and its configuration:
- `domain_id`: Unique domain identifier (e.g. `domain_acoustic_lab`, `domain_ultrasonic`).
- `domain_version`: Version of the domain specification.
- `description`: Semantic description of the domain scope.
- `representation_version`: Supported representation schema version.
- `declared_providers`: Whitelist of ML providers configured for the domain.
- `metadata`: Domain-specific metadata.

`LearningDomain` represents boundary scope; it does not carry execution authority.

### 2.2 Explicit Domain Registration (Fail Closed)
- Unknown domains fail closed immediately (`AdaptiveLearningFailure` with `error_code = "UNREGISTERED_DOMAIN"`).
- Dynamic creation of domains by passing arbitrary strings in API calls is rejected.
- The legacy `"default"` domain is pre-registered for AL1 backward compatibility; it is **not a wildcard** and does **not grant cross-domain access**.

### 2.3 Provider Declarations vs. Real Compatibility
Declaring a compatible provider in `LearningDomain.declared_providers` is metadata only. The `LearningTransferEngine` evaluates:
- Source and target domain separation.
- Representation schema compatibility (major version matching).
- Provider parameter compatibility and translation requirements.
- Knowledge artifact suitability (`KnowledgeType` and `TransferType`).

---

## 3. The AL2 Knowledge Transfer Lifecycle

```text
               SOURCE DOMAIN (Alpha)                       TARGET DOMAIN (Beta)
          ┌─────────────────────────────┐             ┌─────────────────────────────┐
          │  Learned Candidate Model    │             │  Active Production Model    │
          │  (status = CANDIDATE)       │             │  (status = ACTIVE, 1.0.0)   │
          └──────────────┬──────────────┘             └──────────────┬──────────────┘
                         │                                           │ (Remains untouched)
                         ▼                                           │
          ┌─────────────────────────────┐                            │
          │  LearningTransferProposal   │                            │
          │  (authority = NONE)         │                            │
          └──────────────┬──────────────┘                            │
                         │                                           │
                         ▼                                           │
          ┌─────────────────────────────┐                            │
          │ TransferCompatibilityResult │                            │
          │ (Score, Risks, Recs, NONE)  │                            │
          └──────────────┬──────────────┘                            │
                         │                                           │
                         ▼                                           │
          ┌──────────────────────────────────────────────────────────┴──────────────┐
          │               instantiate_transfer_candidate()                          │
          │  Target ModelCandidate (domain = Beta, status = CANDIDATE, NONE)        │
          └──────────────────────────────┬──────────────────────────────────────────┘
                                         │
                                         ▼
                          ┌─────────────────────────────┐
                          │   Target Domain Evaluation  │
                          │   (ModelEvaluation, NONE)   │
                          └──────────────┬──────────────┘
                                         │
                                         ▼
                          ┌─────────────────────────────┐
                          │   ModelPromotionProposal    │
                          │   (authority = NONE)        │
                          └──────────────┬──────────────┘
                                         │
                                         ▼
                          ┌─────────────────────────────┐
                          │    TransferDecisionRecord   │
                          │  (decision_source=EXTERNAL) │
                          │  (cognitia_authority=NONE)  │
                          └──────────────┬──────────────┘
                                         │
                                         ▼
                          ┌─────────────────────────────┐
                          │  Optional Domain Activation │
                          │  (External Host Authority)  │
                          └─────────────────────────────┘
```

---

## 4. Key Contracts and Dataclasses

| Contract / Dataclass | Purpose | Authority Model |
| :--- | :--- | :--- |
| `LearningDomain` | Bounded semantic scope and provider configuration | Scope metadata |
| `LearningTransferProposal` | Explicit advisory proposal to transfer knowledge across domains | `authority = "NONE"` |
| `TransferCompatibilityResult` | Factual evaluation of representation & provider compatibility | `authority = "NONE"` |
| `TransferDecisionRecord` | Audit trail of external domain authority transfer decisions | `decision_source = "EXTERNAL"`, `cognitia_authority = "NONE"` |
| `ModelCandidate` | Scoped candidate model generated by learning or transfer | `authority = "NONE"`, `status = CANDIDATE` |
| `ModelPromotionProposal` | Advisory recommendation comparing candidate against baseline | `authority = "NONE"` |

---

## 5. Gateway HTTP API (AL2 Endpoints)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/v1/learning/domains` | List all explicitly registered learning domains |
| `POST` | `/v1/learning/domains` | Register a new explicit learning domain |
| `GET` | `/v1/learning/transfer/proposals` | List cross-domain transfer proposals |
| `POST` | `/v1/learning/transfer/proposals` | Create an explicit cross-domain transfer proposal |
| `POST` | `/v1/learning/transfer/evaluate` | Evaluate compatibility for a transfer proposal |
| `POST` | `/v1/learning/transfer/instantiate-candidate` | Create target candidate from approved proposal (Active model untouched) |
| `GET` | `/v1/learning/transfer/decisions` | List external transfer decision records |
| `POST` | `/v1/learning/transfer/decision` | Record external transfer governance decision |
| `POST` | `/v1/learning/transfer/activate` | **403 FORBIDDEN**: Activation is external authority only |

---

## 6. Durable File Persistence (P1) Integration

All AL2 domain registrations, transfer proposals, compatibility results, target candidates, and transfer decisions are durably appended to Cognitia's append-only journal (`FilePersistenceService`) before in-memory state updates.

On startup/restart, `EpistemicBridge` replays all journal records, fully restoring multi-domain structures, model candidate lineages, and external transfer audit trails without data loss.
