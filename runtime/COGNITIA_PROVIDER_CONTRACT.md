# Cognitia Provider Contract & Specification

**Contract Version:** 1.0.0  
**Target ABI:** 1.0.0  

---

## 1. Provider Registration Record

Every provider connecting to Cognitia must have a registered provider definition:

```json
{
  "provider_id": "thorium.browser",
  "provider_name": "Lean Thorium Reference Browser",
  "provider_version": "138.0.7204.306",
  "adapter_version": "1.0.0",
  "supported_abi_versions": ["1.0.0"],
  "capabilities": [
    "observe.navigation",
    "observe.tab",
    "observe.page_metadata",
    "observe.authorized_content"
  ],
  "authority_level": "NONE",
  "transport": "local_http"
}
```

---

## 2. Authority Gating

- **`authority_level = "NONE"` (Mandatory):** No provider can grant itself command execution privileges.
- Capability identifiers must follow domain namespaces (e.g., `observe.<domain>`, `propose.<domain>`).
- Prohibited capabilities: `execute.*`, `control.*`, `system.*`, `admin.*`.

---

## 3. Reference Provider: Lean Thorium Adapter

The Lean Thorium browser adapter (located at `E:\Thorium`) is the canonical reference implementation.

- **Phase 3A Capability:** `observe.navigation` (passive navigation events: URL, title, transition type).
- **Phase 3B Capability:** `observe.authorized_content` (explicit user-requested page extraction, bounded to 256 KB, tagged as untrusted external content).