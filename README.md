# Swapnil AI Labs — Agent Language & Gateway
Experimental research preview v0.7 • 25 November 2026

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

Public MIT-licensed experimental project; third-party materials retain their own terms. Do not deploy with sensitive workloads. No claims of novelty or superiority.

## v0.4 research platform
[Context selection, memory, routing and persistent authorization](intelligence/README.md) · [Browser playground](website/playground.html) · [Commercial pilot](distribution/COMMERCIAL_PILOT.md). Runtime acceptance and independent evaluation remain separate from experimental source publication.

## v0.5 — integrated platform foundation
Run `python -m swapnil_ai_labs.demo` and `python -m unittest -v swapnil_ai_labs.test_platform` from the repository root. The offline fixture provider is not a real model. See [architecture](docs/PLATFORM_ARCHITECTURE.md), [research standard](docs/RESEARCH_STANDARD.md), [threat model](docs/THREAT_MODEL.md), [roadmap](docs/PRODUCT_ROADMAP.md) and [changelog](CHANGELOG.md). Generate the evidence inventory with `python research/evidence_manifest.py`. Netlify is deferred. Production acceptance remains pending.

## v0.6 engineering tools
Run `python -m swapnil_ai_labs.engineering_demo`. See [engineering tools](docs/ENGINEERING_TOOLS.md) and [customer use cases](docs/USE_CASES.md). Compiler supports a fixed workflow order, not general optimization. Evaluation uses authored fixtures. Netlify remains deferred.

## Open-source ecosystem v0.7
[MIT license](LICENSE) · [Contributing](CONTRIBUTING.md) · [Component catalog](docs/COMPONENT_CATALOG.md) · [Ecosystem strategy](docs/ECOSYSTEM_STRATEGY.md) · [Third-party notices](THIRD_PARTY_NOTICES.md). Additional independent prototypes: scoped cache, knowledge graph, extractive compression, local message protocol and offline improvement gate. Run `python -m unittest -v intelligence.test_future_components`. Netlify deferred.
