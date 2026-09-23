# Cognitia Standalone Runtime

**Runtime / Product Identity:** `Cognitia`  
**Docker Service / Container Name:** `cognitia`  
**Docker Image:** `cognitia:1.0.0`  
**Cognitive ABI Version:** `1.0.0`  
**Protocol Version:** `1.0.0`  
**Implementation Directory:** `E:\Cognitia\runtime`  
**Core Repository:** `E:\Cognitia`  

---

## 1. Architectural Overview

Cognitia is a standalone epistemic service. External applications (such as the Lean Thorium browser, Frappe ERP, and AcoustiForge) connect as independent providers via canonical adapter boundaries.

```
                    COGNITIA
              Standalone Runtime
                       │
              Canonical ABI 1.0.0
                       │
          ┌────────────┼────────────┐
          │            │            │
       Thorium       Frappe     AcoustiForge
       Adapter       Adapter       Adapter
          │            │            │
          └────────────┼────────────┘
                       │
                Cognitia Core
                       │
              Epistemic Layer
                       │
             Directional Layer
                       │
                Advisory only
```

### Core Invariants
1. **Epistemic Novelty ≠ Production Authority:** Cognitia reasons over observations, manages evidence, and evaluates directional specifications. It has **zero** autonomous authority to execute system commands, control browsers, or modify operating environments.
2. **Untrusted External Content:** External data (e.g. web pages extracted by Thorium) remains strictly inert data (`is_untrusted_external_content = true`). It never acquires instruction or command authority.
3. **Local-First Boundary:** Host exposure is bound strictly to `127.0.0.1`. No public network interfaces (`0.0.0.0`) are exposed.
4. **Identification vs. Authentication:** `X-Cognitia-Provider-Id` identifies the provider for capability whitelist lookup. It does not claim cryptographic authentication. Dynamic registration is disabled.

---

## 2. Quick Start

### Running via Docker Compose
```powershell
cd E:\Cognitia\runtime
docker compose up -d
```

### Verifying Container State
```powershell
docker ps
docker inspect cognitia
```

### Health Check
```powershell
python E:\Cognitia\runtime\scripts\health_check.py http://127.0.0.1:8000/v1/health
```

### Stopping Runtime
```powershell
docker compose down
```

---

## 3. Directory Layout

```
runtime/
├── Dockerfile                   # Minimal python:3.12-slim non-root container
├── compose.yaml                 # Service: cognitia, Container: cognitia, Image: cognitia:1.0.0
├── README.md                    # This document
├── COGNITIA_RUNTIME_ARCHITECTURE.md
├── COGNITIA_PROVIDER_CONTRACT.md
├── COGNITIA_RUNTIME_SECURITY.md
├── COGNITIA_RUNTIME_PROTOCOL.md
├── COGNITIA_RUNTIME_TEST_REPORT.md
├── config/
│   ├── runtime_config.json      # Host binding, limits, rates, memory capacity
│   └── provider_whitelist.json  # Authoritative provider & capability whitelist
├── gateway/
│   ├── __init__.py
│   ├── abi_validator.py         # Canonical ABI v1.0.0 & transport validator
│   ├── provider_registry.py     # Thread-safe static provider & capability gating
│   ├── security.py              # Thread-safe rate limiting, credential scan, untrusted tagging
│   ├── epistemic_bridge.py      # Thread-safe bridge to InMemoryEpistemicService & Directional
│   └── app.py                   # REST API server (127.0.0.1:8000)
├── schemas/
│   ├── observation_abi_v1.json
│   ├── evidence_abi_v1.json
│   ├── directional_spec_abi_v1.json
│   └── provider_contract_v1.json
├── scripts/
│   ├── start_runtime.py
│   └── health_check.py
└── tests/
    ├── test_abi_and_registry.py
    ├── test_concurrency_and_memory.py
    ├── test_epistemic_and_directional.py
    ├── test_gateway_e2e.py
    ├── test_security_and_resilience.py
    └── test_thorium_reference.py
```