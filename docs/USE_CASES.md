# Swapnil AI Labs — customer use cases
Experimental developer infrastructure, not a consumer chatbot or a production security product.

## Finance operations: first pilot
A finance operator requests a read of an authorized invoice. The application host authenticates the operator (future production responsibility), establishes tenant and invoice scope and grants one read. The compiler validates the workflow order and limits. Context selection retrieves relevant documentation; memory retrieves the scoped display preference; the router chooses an eligible provider using configured estimates. The model proposes a structured invoice lookup. The gateway checks exact request binding, grant, expiry and remaining budget before a parameterized, scoped read. The evaluation engine measures correct authorized tasks and unsafe execution separately. The debugger explains blocked requests without loosening controls. Observability records aggregate latency and selected words, not raw prompts.
Current runnable demo uses synthetic SQLite data and a deterministic fixture provider. A previous standalone CPU model experiment is documented separately. No customer data, actual accounting integration, payment or privileged production action.

## Target customers and proposed pilot boundaries
| Buyer | Problem | Proposed integration | Measurable outcome |
|---|---|---|---|
| AI SaaS engineering lead | Unsafe or unreliable tool calls | Put gateway between agent and read-only tools | Authorized task success, unsafe execution rate |
| Automation agency / n8n developer | Workflow failures and hard-to-debug agent decisions | Local HTTP or MCP adapter, then isolated deployment | Failure categories, recovery time |
| Enterprise finance/ops lead | Cross-account data and approval risks | Authorized invoice/report read | Correct scoped reads, audit completeness |
| RAG product engineer | Large irrelevant contexts | Context selector and tenant-scoped memory | Retrieval recall, real token usage, quality |
| AI platform lead | Provider price/latency trade-offs | Model adapter and routing policy | Measured cost, latency, success |
| Researcher/student | Need reproducible agent evaluations | Synthetic harness and evidence manifest | Reproducible runs and transparent limitations |

The narrow finance demo is implemented; other integrations are proposed use cases, not deployed customers. Healthcare may be considered only for non-sensitive synthetic administrative workloads; no HIPAA claim. Start with developer design partners, not a mass-market chatbot.

## Run
python -m swapnil_ai_labs.engineering_demo

## Pilot commercial assumptions
Propose a scoped paid engineering pilot only after a technical discovery call and agreement on acceptance metrics. No guaranteed cost savings or security outcomes. Do not publish client information without permission.
