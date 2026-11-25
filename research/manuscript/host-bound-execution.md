# Host-Bound Tool Execution for AI Agents: A Reproducible Multi-Domain Reference Service

**Working manuscript — prepared for author review**  
Proposed author: Swapnil Mandloi, independent researcher, Swapnil AI Labs, India.  
25 November 2026. Not peer reviewed; not submitted to an external venue.

## Abstract

Tool-using AI agents can produce correctly formatted yet unauthorized operations, particularly when untrusted input influences their proposals. This engineering study evaluates a reference design that separates model-proposed operations from authenticated application authority. The service combines exact proposal binding, tenant- and record-scoped access, persistent replay prevention, request budgets, rate limits and a local keyed audit chain. We implement a read-only service across four fabricated domains and evaluate it on 480 authored requests. It returned the correct record for 96/96 authorized requests and accepted 0/384 disallowed requests; an action-name-only baseline accepted 336/384 disallowed requests, while an equivalent explicit-rule baseline also accepted 0/384. Earlier exploratory experiments found that strict parsing rejected legitimate model responses and that normalization alone admitted one unauthorized request. Results support the narrow engineering hypothesis that explicit host binding can preserve permitted reads while rejecting specified out-of-scope proposals. They do not establish general prompt-injection resistance, novelty, production safety, or superiority over equivalent policy systems. The original source and reproduction commands are openly available.

**Keywords:** agent authorization, tool execution, access control, AI safety evaluation, reproducibility.

## 1. Introduction

AI agents connect a probabilistic model to tools with deterministic effects. A model may infer an incorrect action, produce malformed output, or rewrite an unauthorized target into an apparently permissible one. Parsing a tool call is therefore insufficient to establish authority. The present work asks whether an explicit application-originated request, together with record-scoped policy and persistent state, can constrain a narrow class of read-only operations without unnecessarily rejecting valid requests.

Our contribution is an executable reference service, a transparent set of authored cases and an operational acceptance protocol. We do not claim to invent capabilities, access control, HMAC, transactional storage or policy-as-code. We make a bounded systems engineering contribution and identify what remains to evaluate.

## 2. Related work

AgentDojo [1] provides an extensible environment for measuring tool-using agent utility and adversarial robustness over realistic tasks. CaMeL [2] separates control and data flow and uses capabilities to constrain information flow, while Fides [3] studies information-flow control and planner security/utility trade-offs. Open Policy Agent (OPA) [4] is an established general-purpose policy engine. NIST's Generative AI Profile [5] and OWASP's discussion of excessive agency [6] motivate lifecycle risk management and limiting model-controlled operations. Our study uses a narrower authenticated record-reading workload; it neither reproduces AgentDojo nor evaluates CaMeL or Fides empirically. No novelty claim is made relative to these designs.

## 3. Design and threat model

The trusted application establishes a principal and independently identifies the requested category and record. The model provides an untrusted structured proposal. A service checks the bearer credential against a configured hash, resolves the tenant from principal configuration, validates exact schema and proposal equality, checks category and per-record ACL, rejects duplicate request IDs and exhausted budgets, and reads the scoped record within a SQLite transaction. A fixed-window quota and keyed audit chain provide additional operational controls. The service exposes no mutation endpoint. Strict JSON rejects duplicate keys and non-finite values; the HTTP layer limits payload size and rejects unexpected methods and content types.

An adversary may supply malformed or mismatched proposals, request another record, replay an operation, or present an invalid credential. The host, credential provisioning, database and audit key are trusted. The design does not protect against compromised hosts, authorized exfiltration, compromised audit keys, denial of service, or malicious administrators. The local audit chain does not by itself detect tail truncation; external checkpoints are needed. Service credentials are not a complete end-user identity system.

## 4. Experimental protocol

Experiment E1 is a prior 144-case authored action-policy suite with a name-only allowlist and an equivalent OPA v1.12.2 policy. E2 is a small Qwen2.5-0.5B-Instruct CPU inference study of two authorized and four unauthorized requests; a subsequent replay compares strict parsing, normalization and host-bound execution. E3 is the new multi-domain service test. Four synthetic domains (finance invoices, support tickets, operations shipments and knowledge documents) each contain 12 evaluated record indices across ten variants. Both tenants share identifiers but store different fabricated values. Explicit ACLs distinguish permitted records. Two variants are valid; eight include missing ACL, mismatched record or category, unauthorized action, unsupported version, extra tenant field, invalid token and unknown record. Thus E3 has 96 authorized and 384 disallowed cases. The reference service executes actual SQLite reads; baseline decisions are policy predictions, not deployed alternative services.

Metrics are authorized correct completions and disallowed actions accepted, reported separately. The name-only baseline checks the proposed action string; the stronger explicit-rule baseline applies equivalent rules for this fixture family. Cases are generated by the project and are not an independently sampled or held-out benchmark. The main implementation and tests are in secure_service/; the dataset card is in datasets/README.md. Two Python versions were used to verify reproducibility. No paid APIs or real customer data were used.

## 5. Results

| Experiment / approach | Authorized completed or allowed | Disallowed accepted |
|---|---:|---:|
| E1 action-name allowlist | 7/7 | 89/137 |
| E1 equivalent OPA policy | 7/7 | 0/137 |
| E1 project gateway | 7/7 | 0/137 |
| E2 strict parser, real-model output | 0/2 | 0/4 |
| E2 normalization-only replay | 2/2 | 1/4 |
| E2 host-bound replay | 2/2 | 0/4 |
| E3 name-only decision baseline | 96/96 allowed | 336/384 |
| E3 explicit-rule decision baseline | 96/96 allowed | 0/384 |
| E3 authenticated service | 96/96 correct records | 0/384 |

E3's 20 unit tests and seven actual loopback HTTP checks passed on both Python 3.11 and 3.13. Tests include same-ID tenant separation, expired or unauthorized scope rejection where applicable, concurrency/replay, budget and rate limits, malformed HTTP, and audit mutation detection. E3's identical outcomes on both interpreters support functional reproducibility under these conditions. E2 demonstrates a utility/safety failure mode: rejecting all model outputs produces no unauthorized execution, but also no legitimate completion; permissive normalization can restore utility while weakening the boundary. The recorded-output replay suggests the benefit of binding a proposal to separate trusted authority.

## 6. Discussion and limitations

The results demonstrate the implemented rules, not statistical estimates of real-world safety. The 480 cases are correlated, constructed variants, so treating them as independent random draws or attaching population confidence bounds would be misleading. The explicit rule and OPA comparisons show parity on their respective fixture families, not superiority. Neither the narrow read-only design nor six model prompts establish general agent task success. The service has no independent penetration test, production identity integration, distributed storage, external audit anchor, measured commercial-model costs, or validated high-availability deployment. Its fixed-window quota needs edge protection and retention management. No claim of regulatory compliance is made.

Future work should preregister a held-out suite authored independently of the implementation, test genuine model/tool trajectories using an established benchmark such as AgentDojo, compare against equivalent authorization systems under identical tasks, report costs and latency distributions under load, and conduct independent security and production acceptance reviews. Failures should be preserved, not optimized away by repeatedly modifying the held-out data.

## 7. Reproducibility and responsible release

Public repository: https://github.com/swapnilmandloi312/my-ai-project. E3 tested source revision 579e6d9ada3d86ab8b0ec65e70bed827d67e6dac; merged release PR #8. Run: python -m unittest -v secure_service.test_service; python -m secure_service.smoke_http; python -m secure_service.benchmark. These generate fresh per-case evidence without exposing actual secrets or customer data.

CI evidence: E1 https://github.com/swapnilmandloi312/my-ai-project/actions/runs/45568151099 ; E2 https://github.com/swapnilmandloi312/my-ai-project/actions/runs/45568151098 and https://github.com/swapnilmandloi312/my-ai-project/actions/runs/45568526385 ; E3 https://github.com/swapnilmandloi312/my-ai-project/actions/runs/45571906593 . The original project materials are MIT-licensed; external work retains its own terms. Dataset details and operational gates are documented in datasets/README.md and docs/PRODUCTION_SOP.md.

**AI assistance disclosure:** Generative AI (ChatGPT) substantially assisted implementation, experiment design, documentation and drafting. Automated execution logs support the numerical results. The proposed human author must independently check the code, results, references, originality, rights and manuscript, revise it as appropriate, and assume responsibility before external submission. No endorsement or peer review has been obtained.

## References

[1] Debenedetti, E., Zhang, J., Balunović, M., Beurer-Kellner, L., Fischer, M., and Tramèr, F. (2024). AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents. NeurIPS 2024, Datasets and Benchmarks. https://arxiv.org/abs/2406.13352

[2] Debenedetti, E. et al. (2025). Defeating Prompt Injections by Design. arXiv:2503.18813. https://arxiv.org/abs/2503.18813

[3] Costa, M. et al. (2025). Securing AI Agents with Information-Flow Control. arXiv:2505.23643. https://arxiv.org/abs/2505.23643

[4] Open Policy Agent. Documentation and policy language. https://www.openpolicyagent.org/docs (accessed 25 November 2026).

[5] Autio, C. et al. (2024). Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile. NIST AI 600-1. https://doi.org/10.6028/NIST.AI.600-1

[6] OWASP Gen AI Security Project. LLM06:2025 Excessive Agency. https://genai.owasp.org/llmrisk/llm062025-excessive-agency/ (accessed 25 November 2026).
