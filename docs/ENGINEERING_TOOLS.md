# Engineering tools v0.6
Compiler: a narrow declarative workflow validator and deterministic plan identifier. It accepts only the supported stage order and bounded configuration; it is not a general-purpose compiler, optimizer or cryptographic attestation.
Evaluation: separates legitimate completion from unsafe execution; reports undefined rates as null when denominators are zero. Labels must come from a trusted evaluator, not from the agent.
Debugger: deterministic error-category mapping and remediation hints; cannot automatically change policies or execute actions.
Observability: aggregates numeric traces, median/p95 local elapsed time and context words. No real provider token/cost data or persistent telemetry backend.
Run python -m unittest -v swapnil_ai_labs.test_engineering and python -m swapnil_ai_labs.engineering_demo.
Next research: independently authored held-out scenarios, stronger baselines, real model integration, measured token/cost/latency, schema evolution, production identity. Semantic caching, knowledge graph, agent communication, self-improvement, low-cost inference, multilingual model and AI operating system are separate research milestones; do not label them completed.
