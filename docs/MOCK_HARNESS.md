# Cognitia ↔ Thorium Mock Protocol Test Harness (Architecture & Guide)

## 1. Overview & Purpose

The **Mock Protocol Test Harness** provides a 100% offline, standalone testing and verification suite for the **Thorium ↔ Cognitia Integration Protocol v1** without requiring a full Chromium compilation or live browser execution.

The harness exercises the complete end-to-end lifecycle:
$$\text{Thorium Observation} \xrightarrow[\text{Named Pipe Framing}]{\text{Client Adapter}} \text{Cognitia Daemon} \xrightarrow[\text{Inference/Learning}]{\text{authority = NONE}} \text{Candidate Proposal} \xrightarrow[\text{Simulated External Actor}]{\text{decision\_source = EXTERNAL}} \text{Execution Observation} \rightarrow \text{State Reconciliation}$$

---

## 2. Harness Components

```text
E:\Thorium\protocol\mock/
  ├── __init__.py                # Package exports
  ├── protocol_types.py          # Python dataclasses, enums, and JSON serialization for Protocol v1
  ├── mock_thorium_adapter.py    # Emulates Thorium C++ BrowserObservationCollector & transport queue
  ├── mock_cognitia_daemon.py    # Emulates Cognitia Daemon Named Pipe receiver & Epistemic Core bridge
  ├── protocol_validator.py      # Schema, version, sequence, and correlation validator
  ├── security_validator.py      # S1-S16 invariant checks, credential scrubbing, and injection detection
  └── replay_harness.py          # Deterministic event recorder and bit-for-bit replay verifier
```

---

## 3. Key Invariants Tested by the Harness

1. **Protocol Framing & Monotonic Ordering**: Strict sequence number verification ($1, 2, 3\dots$), duplicate detection, and gap detection.
2. **Correlation & Causal Lineage**: End-to-end trace tracking from observation to proposal, authorization, and execution.
3. **Security Invariants (S1–S16)**:
   - Untrusted web content treated as raw data.
   - Userinfo (`user:pass@host`) and 18 sensitive query keys scrubbed.
   - Zero credentials, cookies, or authorization headers permitted over IPC.
4. **Authority Invariant**:
   - `CandidateActionProposal.authority == "NONE"`.
   - `ExecutionAuthorizationObserved.decision_source == "EXTERNAL"`.
   - Zero autonomous browser execution channels.
5. **Deterministic Replay**: Identical input sequence produces bit-for-bit identical message ordering, fingerprints, and audit traces.
