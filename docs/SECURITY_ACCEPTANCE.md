# Security and guardrail acceptance matrix
| Boundary | Implemented | Remaining before production |
|---|---|---|
| Authentication | High-entropy bearer-token hash comparison | OIDC/service workload identity, secret management and rotation |
| Authorization | Host-bound proposal, principal category and per-record ACL, tenant derived from principal | End-user consent and identity mapping, external policy review |
| Input | Strict JSON, duplicate/nonfinite rejection, size limit, exact shape, no write endpoint | Edge timeout/size limits, fuzzing, API gateway integration |
| State | Atomic request replay, persistent per-principal budget and fixed-window quota | Distributed storage, retention, load/failover testing |
| Audit | HMAC-chained redacted local decisions | External immutable checkpoints, key lifecycle, retention |
| Data | Fabricated records; no sensitive payload telemetry | Classification, encryption, DLP, provider consent, legal/compliance review |
| Model | Exact structured proposal binding | Real-model and independent prompt-injection benchmark |
| Supply chain | Pinned build dependencies, CI | SBOM, signing, independent dependency scan and deployment hardening |
Reference sources: OWASP LLM Top 10 (prompt injection/excessive agency) https://genai.owasp.org/llm-top-10/ ; OPA https://www.openpolicyagent.org/docs ; AgentDojo https://arxiv.org/abs/2406.13352 . These are design references, not compliance certifications.
