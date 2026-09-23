# Cognitia Adaptive Learning - Security Boundary

## 1. Threat Model & Untrusted Inputs

External telemetry, web pages (e.g. from Thorium observations), and sensor payloads are classified as **untrusted data**.

```text
External Web / Telemetry
          ↓
  Untrusted Observation
          ↓
Representation Adapter  ──> [Redacts prompt injection, shell escapes, tokens, credentials]
          ↓
  Sanitized Model Input
          ↓
    Laya Provider
          ↓
Advisory Learning Result (authority = NONE)
```

## 2. Security Boundaries Enforced

1. **No Code Execution**: Model outputs cannot trigger execution directives, shell commands (`rm`, `powershell`, `cmd.exe`), or dynamic python execution (`eval`, `exec`).
2. **Credential Redaction**: `RepresentationAdapter` identifies and redacts authorization headers, Bearer tokens, GitHub tokens, API keys, and session cookies.
3. **No Automatic Network Downloads**: Zero automated model downloads or remote runtime dependencies. Local-first and offline execution only.
4. **Advisory Authority Isolation**: Output dataclasses strictly validate `authority == "NONE"`, rejecting any attempt to claim execution authority.
