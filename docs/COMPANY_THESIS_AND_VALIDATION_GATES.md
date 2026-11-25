# Swapnil AI Labs — company thesis and validation gates
Proposed founder strategy, 25 November 2026. This is a decision document, not a product release or market validation.

## Mission and vision
Vision: a world where intelligence can act reliably, responsibly and at scale.
Mission: build open, model-independent AI infrastructure that transforms intelligence into secure, verifiable and accountable real-world outcomes.
Principle: Intelligence is not enough. Execution must be trustworthy.
Positioning: independent execution and evidence infrastructure for AI agents; Work Relay is the initial business application, not a generic automation catalogue.

## What is verified, and what is not
Main at 3f344902149f95d2060a7e50025f62718187fce0 includes local read-only authorization runtime, persistent Work Relay state machine, SDK/container demo, reviewer-only evidence bridge and two actual small-model comparisons. Four authorized and four unauthorized host-scope cases per approach and four refusal probes are authored and reused; they do not establish independent performance. Qwen exact READ completed 4/4 and emitted 0/4 inappropriate READ proposals; SmolLM2 completed 4/4 and emitted 3/4 inappropriate READ proposals. Host-denied tasks did not invoke the model. Work Relay bridge uses deterministic test providers. No production certification, paying customers, independent audit, public benchmark, owned foundation model, or external manuscript submission verified.

## Market and technical prior art
- AWS AgentCore already provides model-independent runtime, identity, policy and observability: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html
- OpenAI Agents SDK has guardrails and tracing: https://openai.github.io/openai-agents-python/guardrails/ and https://openai.github.io/openai-agents-python/tracing/
- Anthropic recommends starting simple and evaluating before adding agent complexity: https://www.anthropic.com/research/building-effective-agents and https://www.anthropic.com/research/demystifying-evals-for-ai-agents
- NIST agent identity/authorization guidance: https://www.nist.gov/blogs/cybersecurity-insights/design-tenets-agent-identity-management-systems
- OWASP agentic threat categories: https://genai.owasp.org/top-10-for-agentic-applications-2026/
- CaMeL and AgentDojo: https://arxiv.org/abs/2503.18813 and https://github.com/ethz-spylab/agentdojo (repository MIT; pin revision and verify individual data/dependency rights before redistribution).
- BFCL tool calling: https://gorilla.cs.berkeley.edu/leaderboard
- Hugging Face agentic eval publication: https://huggingface.co/blog/agentic-evals and https://huggingface.co/docs/hub/eval-results
- YC user-driven MVP: https://www.ycombinator.com/library/4D-yc-s-essential-startup-advice
- IndiaAI compute/datasets/safe AI support: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2291062&lang=1&reg=1 ; Startup India recognition: https://www.startupindia.gov.in/content/sih/en/startupgov/startup_recognition_page.html . Eligibility and application not verified.

## Proposed product and research portfolio (working names, trademark checks pending)
1. Trusted Intelligence Runtime: core authority, independent policy evaluation, context, durable execution and audit. Open MIT foundation; standards-compatible adapters.
2. Work Relay: first application for finance/operations exception approvals. Choose one narrow paid pilot before adding HR/IT/support.
3. Evidence and Evaluation Lab: independent heldout benchmark, raw traces, failure taxonomy, model/dataset cards, repeatable scoring and public dashboard; no leaderboard claim until published.
4. Control Plane: proposed enterprise admin console for policy, agent identity, approval, cost, incident response and evidence export; not built.
5. India-centric research: consented/licensed multilingual task evaluation and efficient local model inference; original model training only with a justified research question, rights, independent benchmark, funding and compute.

## Priority gates
P0-01 Independent intent and delegated authority: bind actor, purpose, operation, target, tenant, expiry and request nonce to host-approved intent; reject stale/replayed/wrong-audience grants, verify independent of model classification. Test revocation and deny-by-default; do not deploy write actions.
P0-02 Evidence integrity: provenance, immutable content hash, version and trusted source; review invalidation; do not equate record presence to verified documents. 
P0-03 Production boundary: OIDC/OAuth, short-lived credentials, secret store, egress policy, per-tenant quotas, isolation, external audit checkpoints, retention/deletion, backup/restore, incident kill switch. Independent security reviewer and deployment permission required.
P0-04 External evaluation: freeze independently authored tasks at pinned revision, review rights, map tasks without changing ground truth, baseline plain model vs rules vs host-bound (also compare established designs where compatible). Report utility, unsafe execution, inappropriate proposals, false denial, latency p50/p95, resource use, costs and uncertainty. Do not compare incomparable metrics; publish raw failures. 
P0-05 Design-partner discovery: target finance invoice exceptions or operations approvals, whichever has stronger direct evidence; 10 interviews, 3 qualified design partners, 1 permissioned synthetic/read-only pilot as proposed goals, not traction. Collect baseline cycle time, rework, exception rate and cost, then measure same outcomes.
P0-06 Manuscript: verify author identity, all references, claims against pinned artifacts; add honest external evaluation and independent reviewer feedback; author approves before submission. No fabricated novelty, affiliation or publication status.
P1-07 Interoperability: MCP adapter with standards-based authorization, n8n integration without sensitive data, one Python and TypeScript client, OTel-style redacted traces. Avoid bypass routes.
P1-08 Deployment: authenticated staging only, no public production writes; database migration strategy and durable jobs/outbox, idempotent connector contract, rollback/compensation plans and fault injection. Explicit customer permission required.
P1-09 Distribution: Hugging Face benchmark dataset/Space with pinned model metadata, license and reproducibility; GitHub package/release signing, security policy and contributor guide; Product Hunt only after runnable public demo and activation flow; YC truthful traction/application; no external submissions without founder verification.
P1-10 Business: unit economics (cost per verified outcome, contribution margin, support burden), proposed open-core + paid managed/VPC platform + implementation services, test willingness to pay before fixed pricing.
P1-11 Corporate foundations: founder reviews IP/employment obligations, entity registration, brand/trademark, privacy terms, licensing/SBOM, accounting and applicable regulatory responsibilities; verify eligibility before Startup India/IndiaAI applications.
P2-12 Research expansion: multilingual English/Hindi/Hinglish evaluation, small model adaptation and quantization; train only after nontrivial measured benefit vs pretrained baseline and budget approval. Keep datasets non-sensitive and lawful.

## Measurement and operating system
North-star: verified successful resolutions per active customer per week (requires customers, currently unmeasured); reliability, unsafe execution, false denials, cycle time, cost and retention tracked separately. First-pilot targets agreed with design partner, not advertised promises. Every experiment records hypothesis, commit/model/dataset revision, baseline, scoring, failures and reproducible output. Every release gate has an owner, evidence, and explicit blocker. P0 before broadening products, P1 in parallel only when safe and nonblocking. Start discovery alongside engineering. No unapproved paid compute, production deployment, real customer data, external submission or outreach from research automation. Preserve existing Netlify site; roadmap alone is not a production release.
