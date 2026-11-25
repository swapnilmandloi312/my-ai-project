# Swapnil AI Labs — platform architecture
Experimental v0.5, not production ready.

Trusted application host → scoped request and one-use grant → context selector → model router → provider adapter → versioned proposal decoder → host-bound persistent authorization → synthetic read-only result.
Memory is tenant-scoped and only trusted host writes are permitted. The router uses supplied estimates; the fixture provider is not an AI model. The trace excludes payloads and credentials, but is not a tamper-evident audit system.

## Architecture decisions
- ADR-001: stable JSON proposal schema, rejecting unknown versions/fields. Future actions get a separate schema and migration tests.
- ADR-002: model-agnostic callable provider boundary. Add providers only with explicit credentials, budget and independent evaluation.
- ADR-003: trusted host establishes identity, record scope, consent and grants. Never let model output grant access.
- ADR-004: local standard-library reference runtime; no cloud dependency for the demo. Container and cloud profiles must remain separate from production identity.
- ADR-005: synthetic fixtures and provenance tracked separately from real, licensed evaluation data.
- ADR-006: default-deny on parse failure and no eligible route. Track utility alongside safety.
- ADR-007: MIT for original project materials; no patent filing or publication of confidential client material without a specific founder decision.
- ADR-008: retain negative results, compare equivalent baselines, and state uncertainties; no claim of novelty without prior-art and independent validation.

## Future milestones and acceptance gates
1. Real-world benchmark: independent human labels, frozen held-out set, equal workload, separate task completion/unsafe executions, latency/cost with confidence intervals.
2. Production identity: OIDC, tenant-scoped authorization, short-lived credentials, rate limits, signed external audit checkpoint, data retention and deletion controls.
3. Packaging: versioned wheel and JS SDK, signed release manifest, pinned dependencies, SBOM, migration and rollback tests; publish only after license decision.
4. Observability: OpenTelemetry-compatible events, redaction review, latency/cost SLOs, alerting, incident response and backup restore drills.
5. Research: context compression against strong retrieval baselines, multilingual dataset with documented consent/license, calibrated routing with real measured model prices, small-model adaptation only after a dataset and compute plan.
6. Customer pilots: start non-sensitive read-only, obtain written scope and acceptance metrics, run shadow evaluation, approve results and case study separately.
7. Website: Netlify explicitly deferred; deploy research portal and sandbox last.
