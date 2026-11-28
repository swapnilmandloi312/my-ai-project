"""Bounded, read-only evidence tools for a trusted host with approved inputs."""

import json
from types import MappingProxyType

from swapnil_ai_labs.forty_profiles import PROFILES
from swapnil_ai_labs.revision_evidence import revision_receipt


# These categories can use review-ready evidence exported by their owners.
EXPORT_SCHEMAS = MappingProxyType({
    "research": "research_export",
    "market_research": "research_export",
    "competitive_intelligence": "research_export",
    "marketing_analytics": "analytics_export",
    "observability": "analytics_export",
    "data_engineering": "analytics_export",
    "knowledge_ops": "document_export",
    "compliance": "document_export",
    "content_strategy": "document_export",
})
TOOL_REGISTRY = MappingProxyType({
    **EXPORT_SCHEMAS,
    "engineering": "git_revision",
    "technical_writing": "git_revision",
})


def _references(category, payload):
    if not isinstance(payload, dict) or not set(payload) <= set(PROFILES[category].checks):
        raise ValueError("invalid evidence fields")
    if any(
        not isinstance(value, str) or not value.strip() or len(value) > 200
        or value.startswith("synthetic:") or any(not char.isprintable() for char in value)
        for value in payload.values()
    ):
        raise ValueError("invalid evidence reference")
    return {key: payload[key] for key in sorted(payload)}


def execute_read_only(category, tool, payload, *, checkout=None):
    """Dispatch host-approved data to an allowlisted, offline adapter."""
    if tool != TOOL_REGISTRY.get(category) or tool is None:
        raise ValueError("tool is outside the category scope")
    refs = _references(category, payload)
    if tool == "git_revision":
        if checkout is None or set(refs) != {"source_revision"}:
            raise ValueError("checkout and source revision required")
        revision_receipt(checkout, category, refs["source_revision"])
    missing = sorted(set(PROFILES[category].checks) - set(refs))
    return {
        "category": category,
        "tool": tool,
        "kind": "evidence_review",
        "recorded_evidence": refs,
        "missing_checks": missing,
        "objective": PROFILES[category].objective,
        "next_action": PROFILES[category].next_action,
        "requires_review": True,
    }


def encode_deliverable(deliverable):
    body = json.dumps(deliverable, sort_keys=True, allow_nan=False)
    if len(body.encode()) > 16384:
        raise ValueError("deliverable exceeds storage limit")
    return body
