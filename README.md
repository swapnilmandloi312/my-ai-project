# Swapnil AI Labs — Independent AI Research & Engineering

**Building intelligence people can trust.** Our flagship research track is the [Trusted Intelligence Runtime](docs/TRUSTED_INTELLIGENCE_RUNTIME.md): host authorization before inference, strict model proposals, and verified read-only execution. See the [research-first strategy](docs/RESEARCH_COMPANY_STRATEGY.md). Existing browser utilities remain an experimental applications lab, not our core technology. Actual model evidence and deployment acceptance are tracked separately.

Experimental research preview v0.8 • 25 November 2026

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

## v0.8 secure service release candidate
[Authenticated read-only service](secure_service/README.md) · [Dataset card](datasets/README.md) · [Production SOP](docs/PRODUCTION_SOP.md) · [Security acceptance](docs/SECURITY_ACCEPTANCE.md). Four synthetic domains, record ACLs, host-bound proposals, persistent replay/budget controls, local audit chain. Run `python -m unittest -v secure_service.test_service`, `python -m secure_service.smoke_http` and `python -m secure_service.benchmark`. Not production-certified or deployed.

## Global ecosystem expansion
Explore the [24-industry roadmap](docs/GLOBAL_ECOSYSTEM.md), [machine-readable product catalog](ecosystem/catalog.json), and [initial interface translations](ecosystem/interface-copy.json). Discover planned applications with `python -m ecosystem.discover --audience farmers`. Catalog entries describe future products, not deployed applications or validated model language support. Existing secure service remains the tested read-only reference.

## Work Relay — functional local pilot
Run `python -m swapnil_ai_labs.relay_demo` for a synthetic, authenticated four-department HTTP walkthrough. [Quickstart](docs/RELAY_QUICKSTART.md) · [API and limitations](docs/WORK_RELAY.md) · [Provider reliability](docs/PROVIDER_RELIABILITY.md). No external execution or public production service.
