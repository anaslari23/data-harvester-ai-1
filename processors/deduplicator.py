from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Tuple


KEY_FIELDS = [
    "company_name",
    "website",
    "email",
    "phone",
    "address",
    "city",
    "state",
    "country",
    "industry",
    "industry_type",
    "description",
    "source",
]

FUZZY_THRESHOLD = 0.85


def _normalize_key(value: str) -> str:
    if not value:
        return ""
    return re.sub(r"[^\w]", "", value.lower().strip())


def _exact_dedupe_key(rec: Dict[str, Any]) -> Tuple[str, str, str]:
    return (
        _normalize_key(rec.get("company_name", "")),
        _normalize_key(rec.get("website", "")),
        _normalize_key(rec.get("email", "")),
    )


def _levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def _similarity(s1: str, s2: str) -> float:
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0

    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0

    distance = _levenshtein_distance(s1, s2)
    return 1.0 - (distance / max_len)


def _is_similar_company(a: str, b: str) -> bool:
    if not a or not b:
        return False

    norm_a = _normalize_key(a)
    norm_b = _normalize_key(b)

    if norm_a == norm_b:
        return True

    if norm_a in norm_b or norm_b in norm_a:
        return True

    if len(norm_a) >= 4 and len(norm_b) >= 4:
        if norm_a[:4] == norm_b[:4]:
            return True

    similarity = _similarity(norm_a, norm_b)
    if similarity >= FUZZY_THRESHOLD:
        return True

    return False


def _records_are_duplicates(rec1: Dict[str, Any], rec2: Dict[str, Any]) -> bool:
    name1 = rec1.get("company_name", "")
    name2 = rec2.get("company_name", "")

    website1 = _normalize_key(rec1.get("website", ""))
    website2 = _normalize_key(rec2.get("website", ""))
    if website1 and website1 == website2:
        return True

    email1 = _normalize_key(rec1.get("email", ""))
    email2 = _normalize_key(rec2.get("email", ""))
    if email1 and email1 == email2:
        return True

    phone1 = re.sub(r"\D", "", rec1.get("phone", ""))
    phone2 = re.sub(r"\D", "", rec2.get("phone", ""))
    if phone1 and phone1 == phone2 and len(phone1) >= 10:
        return True

    if name1 and name2 and _is_similar_company(name1, name2):
        return True

    return False


def _merge(primary: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(primary)
    for key in KEY_FIELDS:
        if not merged.get(key) and incoming.get(key):
            merged[key] = incoming[key]

    if not merged.get("company_name") and incoming.get("company_name"):
        if len(str(incoming["company_name"])) > len(
            str(merged.get("company_name", ""))
        ):
            merged["company_name"] = incoming["company_name"]

    if primary.get("additional_info") and incoming.get("additional_info"):
        extras = [str(primary["additional_info"]), str(incoming["additional_info"])]
        merged["additional_info"] = " | ".join(dict.fromkeys(extras))
    elif incoming.get("additional_info"):
        merged["additional_info"] = incoming["additional_info"]

    return merged


def deduplicate(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    record_list = list(records)

    merged_by_key: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    ordered_keys: List[Tuple[str, str, str]] = []

    for rec in record_list:
        key = _exact_dedupe_key(rec)
        if key not in merged_by_key:
            merged_by_key[key] = dict(rec)
            ordered_keys.append(key)
        else:
            merged_by_key[key] = _merge(merged_by_key[key], rec)

    result = list(merged_by_key.values())

    unique: List[Dict[str, Any]] = []
    for rec in result:
        is_dup = False
        for existing in unique:
            if _records_are_duplicates(existing, rec):
                unique[unique.index(existing)] = _merge(existing, rec)
                is_dup = True
                break
        if not is_dup:
            unique.append(rec)

    return unique


def deduplicate_exact(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged_by_key: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    ordered_keys: List[Tuple[str, str, str]] = []

    for rec in records:
        key = _exact_dedupe_key(rec)
        if key not in merged_by_key:
            merged_by_key[key] = dict(rec)
            ordered_keys.append(key)
        else:
            merged_by_key[key] = _merge(merged_by_key[key], rec)

    return [merged_by_key[key] for key in ordered_keys]
