# Swapnil AI Labs — Agent Language & Gateway
Experimental research preview v0.3 • 25 November 2026

Contract-first language and reference gateway for controlled AI tool execution. Includes a real read-only SQLite integration using synthetic data, an opt-in OpenAI-compatible HTTP adapter tested with a local fixture server, and committed synthetic research evidence. No production security claim, real LLM benchmark, customer data or external API calls.

## Run
Python 3.13. Core and pilot use the standard library.
```sh
python -m unittest -v test_agent_language.py
python -m unittest discover -v -s tests
python -m integrations.pilot
python research/verify_evidence.py
```
See [report](research/REPORT.md), [raw evidence](research/raw-results.jsonl), [reproducibility](research/REPRODUCIBILITY.md), [integration](integrations/PRODUCT.md), [security](SECURITY.md), [website](website/index.html) and [launch drafts](distribution/PILOT_LAUNCH.md). The previous local launch package includes the five experiment generators.

Public experimental preview; license decision pending. Do not deploy with sensitive workloads. No claims of novelty or superiority.
