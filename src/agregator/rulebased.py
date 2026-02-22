# src/aggregator/rulebased.py
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from src.logger import get_logger
from src.config import DEFAULT_RULES

logger = get_logger(__name__)


def group_key_for_finding(f: Dict) -> str:
    """
    Группируем по (url, form_index, field_name).
    """
    url = str(f.get("url") or "")
    form_index = str(f.get("form_index") or "")
    field = str(f.get("field_name") or "")
    return "|".join([url, form_index, field])


def compute_group_score(group: List[Dict], rules: Dict) -> Tuple[float, List[str]]:
    """
    Простая детерминированная формула:
      score = max(severity_weight) + payload_bonus + sql_bonus + time_bonus
    Возвращает (score, notes).
    """
    if rules is None:
        rules = DEFAULT_RULES

    weights = rules.get("weights", DEFAULT_RULES["weights"])
    bonuses = rules.get("bonuses", DEFAULT_RULES["bonuses"])
    td_threshold = rules.get(
        "time_delay_threshold_ms", DEFAULT_RULES["time_delay_threshold_ms"]
    )

    # severity base (максимальная по весу)
    severities = [it.get("severity") for it in group if it.get("severity")]
    severity_weights = [weights.get(s, 0) for s in severities]
    base = max(severity_weights) if severity_weights else 0

    # unique payloads
    payload_ids = {f.get("payload_index") for f in group if f.get("payload_index")}
    unique_payloads = len([p for p in payload_ids if p])

    # match types count
    match_types = {f.get("match_type") for f in group if f.get("match_type")}
    distinct_match_types = len([m for m in match_types if m])

    # evidence-based flags (используем поля уже подготовленные при нормализации, если есть)
    has_sql = any(True for f in group if f.get("has_sql_signature"))
    has_time_delay = any(
        (f.get("response_time") or 0) >= td_threshold
        or f.get("is_time_based_candidate")
        for f in group
    )

    score = float(base)
    notes: List[str] = []

    # бонусы
    if unique_payloads >= 2:
        payload_bonus = bonuses.get("multiple_payloads", 0) * min(unique_payloads, 5)
        score += payload_bonus
        notes.append(f"unique_payloads={unique_payloads}")
    if has_sql:
        score += bonuses.get("sql_error", 0)
        notes.append("sql_error")
    if has_time_delay:
        score += bonuses.get("time_delay", 0)
        notes.append("time_delay")
    if distinct_match_types >= 2:
        score += bonuses.get("distinct_match_types", 0)
        notes.append(f"distinct_match_types={distinct_match_types}")

    score = min(score, rules.get("max_score", 20))
    return score, notes


def aggregate_findings(findings: List[Dict], rules: Optional[Dict] = None) -> Dict:
    """
    Агрегирует normalized findings (список dict).
    Возвращает структуру с groups и summary.
    Формат выходных групп минимален и JSON-совместим.
    """
    if rules is None:
        rules = DEFAULT_RULES

    groups_map: Dict[str, List[Dict]] = defaultdict(list)
    for f in findings:
        key = group_key_for_finding(f)
        groups_map[key].append(f)

    groups_out: Dict[str, Dict] = {}

    for key, items in groups_map.items():
        count = len(items)
        unique_payloads = len(
            {it.get("payload_index") for it in items if it.get("payload_index")}
        )

        # агрегированная severity (максимальная по весу)
        weights = rules.get("weights", DEFAULT_RULES["weights"])
        severities = [it.get("severity") for it in items if it.get("severity")]
        severity_agg = None
        if severities:
            severity_agg = max(severities, key=lambda s: weights.get(s, 0))

        score, notes = compute_group_score(items, rules)

        groups_out[key] = {
            "count": count,
            "unique_payloads": unique_payloads,
            "severity_agg": severity_agg,
            "score": score,
            "notes": notes,
        }

        logger.debug(
            "group computed", extra={"group_key": key, "count": count, "score": score}
        )

    summary = {
        "total_findings": len(findings),
        "total_groups": len(groups_out),
        "top_groups": sorted(
            [{"group_key": k, "score": v["score"]} for k, v in groups_out.items()],
            key=lambda x: x["score"],
            reverse=True,
        )[:5],
    }

    return {"groups": groups_out, "summary": summary}
