"""Bounded public bibliographic evidence for one approved Crossref DOI."""

import http.client
import json
import re
from urllib.parse import quote

HOST = "api.crossref.org"
MAX_BYTES = 2 * 1024 * 1024
DOI = re.compile(r"10\.[0-9]{4,9}/[-._;()/:A-Z0-9]+", re.ASCII | re.IGNORECASE)


def _text(value, limit=500):
    if not isinstance(value, str):
        return ""
    return "".join(char for char in value[:limit] if char.isprintable()).strip()


def _first_text(value):
    return _text(value[0]) if isinstance(value, list) and value else ""


def _publication_year(record):
    issued = record.get("issued")
    dates = issued.get("date-parts") if isinstance(issued, dict) else None
    if dates and isinstance(dates, list) and isinstance(dates[0], list) and dates[0]:
        year = dates[0][0]
        if type(year) is int and 1 <= year <= 9999:
            return year
    return None


def bibliography(doi):
    """Fetch the deposited citation and basic metadata for a literal DOI."""
    if not isinstance(doi, str) or len(doi) > 180 or DOI.fullmatch(doi) is None:
        raise ValueError("a literal Crossref DOI is required")

    connection = http.client.HTTPSConnection(HOST, timeout=6)
    try:
        connection.request(
            "GET", "/works/" + quote(doi, safe=""),
            headers={"Accept": "application/json", "User-Agent": "Swapnil-AI-Labs-Research/1.0"},
        )
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError(f"Crossref lookup failed (HTTP {response.status})")
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("Crossref response exceeds size limit")
        payload = json.loads(raw)
    except (OSError, http.client.HTTPException, UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError("Crossref metadata request failed") from None
    finally:
        connection.close()

    record = payload.get("message") if isinstance(payload, dict) and payload.get("status") == "ok" else None
    returned_doi = record.get("DOI") if isinstance(record, dict) else None
    if not isinstance(returned_doi, str) or returned_doi.casefold() != doi.casefold():
        raise ValueError("Crossref response does not match approved DOI")

    author_list = record.get("author")
    authors = []
    if isinstance(author_list, list):
        for author in author_list[:8]:
            if isinstance(author, dict):
                name = _text(author.get("name"), 96) or " ".join(filter(None, (
                    _text(author.get("given"), 48), _text(author.get("family"), 48),
                )))
                if name:
                    authors.append(name)
    title = _first_text(record.get("title"))
    if not title:
        raise ValueError("Crossref record has no citation title")

    return {
        "deliverable_type": "bibliographic_record",
        "source": "crossref",
        "doi": returned_doi.lower(),
        "citation_url": "https://doi.org/" + quote(returned_doi.lower(), safe="/"),
        "title": title,
        "publication": _first_text(record.get("container-title")),
        "publication_year": _publication_year(record),
        "work_type": _text(record.get("type"), 64),
        "authors": authors,
        "author_list_truncated": isinstance(author_list, list) and len(author_list) > 8,
    }
