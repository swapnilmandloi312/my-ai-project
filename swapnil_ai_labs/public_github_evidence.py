"""Credential-free, read-only access to the approved public GitHub repository."""

import http.client
import json
import os
import re


REPOSITORY = "swapnilmandloi312/my-ai-project"
MAX_RESPONSE = 1024 * 1024
GITHUB_CATEGORIES = frozenset({
    "engineering", "technical_writing", "architecture", "automation", "backend", "devops", "frontend", "quality",
})


def public_revision_deliverable(category, revision):
    if category not in GITHUB_CATEGORIES:
        raise ValueError("category is outside the public GitHub scope")
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("full GitHub commit SHA required")
    connection = http.client.HTTPSConnection("api.github.com", timeout=5)
    try:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "Swapnil-AI-Labs-Evidence-Worker",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        token = os.environ.get("SAL_GITHUB_READ_TOKEN")
        if token:
            headers["Authorization"] = "Bearer " + token
        connection.request("GET", f"/repos/{REPOSITORY}/commits/{revision}?per_page=30", headers=headers)
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError(f"public commit unavailable (HTTP {response.status})")
        raw = response.read(MAX_RESPONSE + 1)
        if len(raw) > MAX_RESPONSE:
            raise ValueError("public commit response exceeds limit")
        paginated = 'rel="next"' in (response.getheader("Link") or "")
        payload = json.loads(raw)
    except (OSError, http.client.HTTPException, UnicodeError, RecursionError):
        raise ValueError("public GitHub request failed") from None
    finally:
        connection.close()
    if not isinstance(payload, dict) or payload.get("sha") != revision:
        raise ValueError("unexpected public commit")
    files = payload.get("files")
    stats = payload.get("stats")
    if not isinstance(files, list) or not isinstance(stats, dict):
        raise ValueError("commit change data missing")
    paths = []
    for item in files[:30]:
        path = item.get("filename") if isinstance(item, dict) else None
        if not isinstance(path, str) or not path or len(path) > 240:
            raise ValueError("invalid change path")
        paths.append(path)
    totals = {key: stats.get(key) for key in ("additions", "deletions")}
    if any(type(value) is not int or value < 0 for value in totals.values()):
        raise ValueError("invalid change totals")

    result = {
        "repository": REPOSITORY,
        "commit": revision,
        "source_url": f"https://github.com/{REPOSITORY}/commit/{revision}",
        "paths_truncated": paginated or len(files) > 30,
    }
    if category == "engineering":
        return {**result, "deliverable_type": "change_impact_review",
                "line_changes": totals, "changed_paths": paths}
    if category == "architecture":
        components = {}
        for path in paths:
            area = path.split("/", 1)[0] if "/" in path else "(repository root)"
            components[area] = components.get(area, 0) + 1
        return {**result, "deliverable_type": "component_impact_inventory",
                "changed_paths_by_component": components,
                "cross_component_review_needed": len(components) > 1}
    if category == "automation":
        workflows = [path for path in paths if path.startswith(".github/workflows/")
                     or path.endswith(("_worker.py", "workflow.json"))]
        return {**result, "deliverable_type": "automation_change_inventory",
                "changed_workflow_and_worker_paths": workflows}
    if category == "backend":
        source = [path for path in paths if path.endswith(".py") and not _is_test(path)]
        schemas = [path for path in paths if path.endswith(".sql") and not _is_test(path)]
        return {**result, "deliverable_type": "backend_release_review",
                "python_source_paths": source, "database_paths": schemas,
                "migration_review_needed": bool(schemas)}
    if category == "devops":
        controls = [path for path in paths if path.startswith((".github/workflows/", "deployment/"))
                    or path.rsplit("/", 1)[-1] in {"Dockerfile", "vercel.json", "netlify.toml"}]
        return {**result, "deliverable_type": "deployment_change_inventory",
                "release_control_paths": controls, "rollback_review_needed": bool(controls)}
    if category == "frontend":
        ui = [path for path in paths if path.endswith((".html", ".css", ".tsx", ".jsx", ".vue"))
              or (path.startswith(("control-center/", "website/")) and path.endswith((".js", ".mjs")))]
        return {**result, "deliverable_type": "frontend_regression_scope",
                "changed_interface_paths": ui,
                "suggested_checks": ["keyboard navigation", "narrow viewport", "session handling"] if ui else []}
    if category == "quality":
        tests = [path for path in paths if _is_test(path)]
        return {**result, "deliverable_type": "test_change_inventory",
                "changed_test_paths": tests, "other_paths_reviewed": len(paths) - len(tests)}
    docs = [path for path in paths if path.lower().startswith("docs/")
            or path.lower().endswith((".md", ".rst", ".adoc"))]
    return {**result, "deliverable_type": "documentation_coverage_review",
            "documentation_paths": docs, "other_paths_reviewed": len(paths) - len(docs)}


def _is_test(path):
    name = path.rsplit("/", 1)[-1]
    return (name.startswith("test_") or name.endswith(("_test.py", "-test.mjs", ".test.js"))
            or "tests" in path.split("/")[:-1])
