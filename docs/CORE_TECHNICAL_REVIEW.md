# Core technical review — 25 November 2026
Source review, not independent audit.
- P0: Evidence presence is not document authenticity: trusted ingestion, content hash, tenant/item/key binding, immutable reviewed revision.
- P0: Separate evidence and workflow stores: enforce versioned snapshot and recheck; no model-granted approval.
- P0: Idempotency replay must recheck current principal scope and bind tenant/role/configuration; review revocation.
- P0: Isolate privileged read endpoints; single policy boundary, OIDC, TLS, credential rotation and egress controls.
- P0: Worker deadline is not sandbox; separate process identity, resource controls, warm supervised serving.
- P0: API rate/tenant/storage limits and load/backpressure tests.
- P1: External audit checkpoints, backup/restore, retention/deletion and encryption; local HMAC cannot detect tail truncation.
- P1: Model refusal probes, multilingual independent holdout, fair deterministic baseline, latency/cost and failure taxonomy.
- P1: Signed provenance, SBOM, dependency scans and repeatable builds.
- P1: Separate authenticated pilot UI; no bearer secrets in public frontend. Netlify remains unchanged.
- P2: Narrow initial finance/support pilot and measure cycle time, exceptions and manual effort; do not invent traction.
