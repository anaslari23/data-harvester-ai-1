"""Structured data extractor for JSON-LD / Schema.org markup.

Extracts company information from <script type="application/ld+json"> blocks
embedded in web pages. Schema.org Organization, LocalBusiness, and related
types carry authoritative data that is far more reliable than regex scraping.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from bs4 import BeautifulSoup

# Schema.org types that represent a business / organization
ORG_TYPES = {
    "Organization",
    "LocalBusiness",
    "Corporation",
    "Store",
    "Restaurant",
    "Hotel",
    "MedicalOrganization",
    "EducationalOrganization",
    "GovernmentOrganization",
    "NGO",
    "SportsOrganization",
    "FoodEstablishment",
    "EntertainmentBusiness",
    "FinancialService",
    "AutoDealer",
    "HomeAndConstructionBusiness",
    "LodgingBusiness",
    "TravelAgency",
}

DECISION_MAKER_ROLES = {
    "ceo", "chief executive", "founder", "co-founder", "cofounder",
    "managing director", "director", "owner", "proprietor",
    "cto", "chief technology", "it head", "head of it",
    "cfo", "chief financial", "finance head", "head of finance",
    "coo", "chief operating", "president", "vice president",
    "partner", "principal",
}


def extract_structured_data(html: str) -> Dict[str, Any]:
    """Extract company fields from JSON-LD schema.org blocks in ``html``.

    Returns a dict with any of: company_name, email, phone, address, city,
    state, country, employee_count, contact_name, description, website.
    Empty strings are not included so callers can use `.get()` safely.
    """
    if not html:
        return {}

    soup = BeautifulSoup(html, "lxml")
    result: Dict[str, Any] = {}

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            raw = script.string or ""
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue

        # Could be a list (e.g. @graph) or a single object
        items: List[Dict[str, Any]] = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            graph = data.get("@graph")
            if isinstance(graph, list):
                items = graph
            else:
                items = [data]

        for item in items:
            if not isinstance(item, dict):
                continue
            _absorb_schema_item(item, result)

    return result


def _absorb_schema_item(data: Dict[str, Any], result: Dict[str, Any]) -> None:
    """Merge fields from a single schema.org item into *result*."""
    schema_type = data.get("@type", "")
    if isinstance(schema_type, list):
        schema_type = schema_type[0] if schema_type else ""

    is_org = schema_type in ORG_TYPES or "Business" in schema_type or "Organization" in schema_type

    if is_org:
        _fill(result, "company_name", data.get("name"))
        _fill(result, "email", data.get("email"))
        _fill(result, "phone", data.get("telephone") or data.get("phone"))
        _fill(result, "website", data.get("url") or data.get("sameAs"))
        _fill(result, "description", _trunc(data.get("description"), 500))

        # Address
        addr = data.get("address")
        if addr and not result.get("address"):
            if isinstance(addr, dict):
                parts = [
                    addr.get("streetAddress", ""),
                    addr.get("addressLocality", ""),
                    addr.get("addressRegion", ""),
                    addr.get("postalCode", ""),
                    addr.get("addressCountry", ""),
                ]
                result["address"] = ", ".join(p for p in parts if p)
                _fill(result, "city", addr.get("addressLocality"))
                _fill(result, "state", addr.get("addressRegion"))
                _fill(result, "country", addr.get("addressCountry"))
            elif isinstance(addr, str):
                result["address"] = addr

        # Employee count
        emp = data.get("numberOfEmployees")
        if emp and not result.get("employee_count"):
            if isinstance(emp, dict):
                val = emp.get("value") or emp.get("minValue")
                if val:
                    result["employee_count"] = str(val)
            elif emp:
                result["employee_count"] = str(emp)

        # Founder → contact_name
        if not result.get("contact_name"):
            _try_extract_contact(data, result)

    elif schema_type == "Person":
        # Stand-alone Person block — check if they have a relevant role
        if not result.get("contact_name") and data.get("name"):
            job_title = str(data.get("jobTitle", "")).lower()
            if _is_decision_maker_role(job_title):
                result["contact_name"] = str(data["name"])


def _try_extract_contact(data: Dict[str, Any], result: Dict[str, Any]) -> None:
    """Try to pull a decision-maker name from various schema.org fields."""
    # founder
    founder = data.get("founder")
    if founder:
        name = _person_name(founder)
        if name:
            result["contact_name"] = name
            return

    # employee / employees list — pick the first with a decision-maker title
    for field in ("employee", "employees", "member", "members"):
        people = data.get(field)
        if not people:
            continue
        if isinstance(people, dict):
            people = [people]
        if isinstance(people, list):
            for person in people:
                if not isinstance(person, dict):
                    continue
                title = str(person.get("jobTitle", "")).lower()
                if _is_decision_maker_role(title) and person.get("name"):
                    result["contact_name"] = str(person["name"])
                    return

    # contactPoint
    contact_point = data.get("contactPoint")
    if contact_point:
        if isinstance(contact_point, dict):
            name = _person_name(contact_point)
            if name:
                result["contact_name"] = name


def _person_name(obj: Any) -> str:
    if isinstance(obj, str):
        return obj.strip()
    if isinstance(obj, dict):
        return str(obj.get("name", "")).strip()
    if isinstance(obj, list) and obj:
        return _person_name(obj[0])
    return ""


def _is_decision_maker_role(title: str) -> bool:
    return any(role in title for role in DECISION_MAKER_ROLES)


def _fill(result: Dict[str, Any], key: str, value: Any) -> None:
    """Set *key* in *result* only if it's not already set and *value* is truthy."""
    if value and not result.get(key):
        result[key] = str(value).strip()


def _trunc(value: Any, max_len: int) -> str:
    if not value:
        return ""
    s = str(value).strip()
    return s[:max_len]
