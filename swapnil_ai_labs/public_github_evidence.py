"""Credential-free, read-only access to the approved public GitHub repository."""

import http.client
import json
import os
import re


REPOSITORY = "swapnilmandloi312/my-ai-project"
MAX_RESPONSE = 1024 * 1024


def public_revision_deliverable(category, revision):
    if category not in {"engineering", "technical_writing"}:
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
    docs = [path for path in paths if path.lower().startswith("docs/")
            or path.lower().endswith((".md", ".rst", ".adoc"))]
    return {**result, "deliverable_type": "documentation_coverage_review",
            "documentation_paths": docs, "other_paths_reviewed": len(paths) - len(docs)}
