"""Forty bounded evidence-review profiles; no model or external actions."""
from types import MappingProxyType
from swapnil_ai_labs.goal_agents import GOALS, GoalSpec

EXTRA = {
    "architecture": ("Review system boundaries", "design interfaces tradeoffs", "Review architecture decision"),
    "backend": ("Validate backend changes", "api_contract tests rollback", "Review backend implementation"),
    "frontend": ("Validate user interface", "screens accessibility tests", "Review interface evidence"),
    "devops": ("Validate deployment readiness", "build deployment rollback", "Review release gate"),
    "data_engineering": ("Validate data pipelines", "schema lineage data_tests", "Review pipeline evidence"),
    "automation": ("Validate workflow reliability", "workflow retry_tests error_paths", "Review workflow"),
    "integration": ("Validate integration contracts", "contract sandbox_tests permission", "Review integration"),
    "observability": ("Review service reliability", "metrics traces alerts", "Review service signals"),
    "incident_response": ("Coordinate incident review", "timeline impact mitigation", "Review incident response"),
    "privacy": ("Review data minimization", "data_inventory retention access_review", "Review privacy controls"),
    "compliance": ("Review compliance evidence", "requirements controls review", "Review obligations"),
    "technical_writing": ("Review technical documentation", "source_revision examples review", "Review documentation"),
    "developer_relations": ("Review developer enablement", "sample_code audience review", "Review educational material"),
    "content_strategy": ("Review content strategy", "audience sources editorial_review", "Review content plan"),
    "video_production": ("Review video production", "script footage_rights quality_check", "Review video package"),
    "seo": ("Review search visibility", "crawl evidence keyword_fit", "Review SEO findings"),
    "marketing_analytics": ("Review marketing performance", "event_schema attribution metrics", "Review campaign evidence"),
    "lead_research": ("Review candidate fit", "organization public_source fit_evidence", "Review prospect qualification"),
    "sales_ops": ("Review pipeline readiness", "opportunity qualification approval", "Review sales pipeline"),
    "customer_success": ("Review customer outcomes", "goal usage feedback", "Review success evidence"),
    "market_research": ("Review market evidence", "sources segment limitations", "Review market findings"),
    "competitive_intelligence": ("Review competitive positioning", "sources comparison limitations", "Review comparison"),
    "procurement": ("Review procurement options", "quotes requirements approval", "Review purchasing options"),
    "legal_ops": ("Prepare legal review materials", "document jurisdiction counsel_review", "Route for legal review"),
    "recruiting": ("Review role requirements", "role_spec screening_rubric consent", "Review recruiting evidence"),
    "knowledge_ops": ("Review knowledge quality", "source provenance freshness", "Review knowledge record"),
}
PROFILES = MappingProxyType({**GOALS, **{
    name: GoalSpec(objective, tuple(checks.split()), action)
    for name, (objective, checks, action) in EXTRA.items()
}})

def evaluate(category, evidence):
    spec = PROFILES[category]
    if not isinstance(evidence, dict) or set(evidence) - set(spec.checks):
        raise ValueError("invalid evidence fields")
    if any(not isinstance(v, str) or not v.startswith("synthetic:") or len(v)>200
           for v in evidence.values()):
        raise ValueError("only synthetic references accepted")
    missing = sorted(set(spec.checks) - set(evidence))
    return {"category": category, "objective": spec.objective,
            "missing": missing, "next_action": spec.next_action,
            "status": "needs_evidence" if missing else "ready_for_independent_review",
            "scope": "synthetic", "external_action": False,
            "verified_completion": False}
