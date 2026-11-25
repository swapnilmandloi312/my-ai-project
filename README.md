# Swapnil AI Labs — Agent Language & Gateway
Experimental research preview v0.5 • 25 November 2026

Contract-first language and reference gateway for controlled AI tool execution. Includes a real read-only SQLite integration using synthetic data, an opt-in OpenAI-compatible HTTP adapter tested with a local fixture server, and committed synthetic research evidence. No production security claim or customer data. The small CPU-model evaluation is exploratory, not an independent benchmark.

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

## v0.4 research platform
[Context selection, memory, routing and persistent authorization](intelligence/README.md) · [Browser playground](website/playground.html) · [Commercial pilot](distribution/COMMERCIAL_PILOT.md). Runtime acceptance and independent evaluation remain separate from experimental source publication.

## v0.5 — integrated platform foundation
Run `python -m swapnil_ai_labs.demo` and `python -m unittest -v swapnil_ai_labs.test_platform` from the repository root. The offline fixture provider is not a real model. See [architecture](docs/PLATFORM_ARCHITECTURE.md), [research standard](docs/RESEARCH_STANDARD.md), [threat model](docs/THREAT_MODEL.md), [roadmap](docs/PRODUCT_ROADMAP.md) and [changelog](CHANGELOG.md). Generate the evidence inventory with `python research/evidence_manifest.py`. Netlify is deferred. License and production acceptance remain pending.
