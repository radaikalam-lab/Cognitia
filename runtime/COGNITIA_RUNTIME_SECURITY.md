# Cognitia Runtime Security Architecture & Threat Model

**Document Version:** 1.0.0  
**Runtime Identity:** `Cognitia`  
**Container:** `cognitia` (`cognitia:1.0.0`)  
**Security Posture:** Minimal Privilege / Local-First / Zero Autonomous Authority  

---

## 1. Threat Model & Principles

1. **Local-Only Host Exposure:**
   - Host binding is strictly `127.0.0.1`.
   - The container internal daemon listens on port 8000; Compose maps host `127.0.0.1:8001 -> 8000`.
   - Public binding `0.0.0.0` on the host interface is strictly prohibited.

2. **Untrusted External Content Isolation:**
   - All observations originating from browser/web extractors (e.g. Lean Thorium) are automatically tagged with `is_untrusted_external_content = true`.
   - Web content is strictly passive text/data; it cannot trigger command execution, system calls, network requests, or prompt elevation.

3. **Zero Autonomous Execution Authority:**
   - Canonical Invariant: **Epistemic Novelty ≠ Production Authority**.
   - Cognitia exposes zero execution APIs (`execute`, `shell`, `system`, `subprocess`, `run_command`).
   - Any payload containing execution keys is rejected with `422 Unprocessable Entity`.

4. **Static Provider Whitelisting (No Dynamic Self-Registration):**
   - All authorized providers and capabilities are statically defined in `runtime/config/provider_whitelist.json`.
   - `POST /v1/providers/register` is permanently disabled in Runtime 1.0 (`403 Forbidden`).
   - Provider header `X-Cognitia-Provider-Id` is provider *identification* for capability lookup, not authentication.

5. **Container Privilege Hardening:**
   - **User:** Non-root service account `cognitia` (UID 10001, GID 10001).
   - **Root Filesystem:** Read-only (`read_only: true`) with minimal ephemeral `tmpfs` at `/tmp`.
   - **Linux Capabilities:** Dropped unconditionally (`cap_drop: ALL`).
   - **Privilege Escalation:** Blocked (`security_opt: [no-new-privileges:true]`).
   - **Host Isolation:** Zero host filesystem mounts, no Docker socket access, no host network namespace, no host PID/IPC sharing.

6. **Credential Leakage Sanitization:**
   - Structured observation payloads are scanned to reject accidental password, API key, auth header, or token leaks.
   - Natural language containing words like "token" or "secret" is safely allowed as content without false positives.

7. **Resource Bounds & DoS Prevention:**
   - Max payload size: 512 KB.
   - Max nesting depth: 10 levels.
   - Max string size: 256 KB.
   - Max object keys: 500 keys.
   - Max array length: 1000 items.
   - Max epistemic memory nodes: 50,000 nodes.
   - Sliding window rate limiting: 600 requests/minute per provider.