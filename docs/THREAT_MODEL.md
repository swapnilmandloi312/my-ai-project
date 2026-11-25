# Threat model — synthetic reference platform
Assets: tenant identity, grants, budget, memory, records, model requests, audit trail. Boundaries: application host, provider, proposal decoder, authorization store and database. Host is trusted in the reference; all model output is untrusted. No external provider is called by the offline demo.
| Threat | Reference control | Missing before production |
|---|---|---|
| Prompt injection or forged action | exact schema, host-bound request | independent adversarial evaluation |
| Cross-tenant access | scoped queries, host tenant check | authenticated tenancy, isolation tests |
| Replay and concurrency | transactional one-use grants | distributed concurrency and key lifecycle |
| Credential leaks | minimal trace without raw payloads/grants | secret store, redaction tests and log access controls |
| Provider cost escalation | estimated router constraints, action budget | metered provider limits and rate limiting |
| Audit alteration | local audit table | externally anchored signing and retention |
| Dependencies and build integrity | CI and SHA-256 inventory | signed artifacts, SBOM, dependency review |
| Context exfiltration | trusted host records in offline demo | document ACLs, provider allowlist, DLP and consent |
| Resource exhaustion | bounded proposal payload | timeouts, quotas, network isolation, cancellation |
Only synthetic data is supported. Do not expose as a public authenticated production endpoint.
