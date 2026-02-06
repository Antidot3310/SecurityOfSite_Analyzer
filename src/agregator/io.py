"""
Модуль для нормализации и экспорта находок."""
from typing import Optional, List
from src.scanner.models import Finding
from src.logger import get_logger

logger = get_logger(__name__)


def normalize_finding(f: Finding, idx: int, scan_id: Optional[int]) -> dict | None:
    """
    Преобразует находку в нормализованный словарь.
    """
    return {
        "finding_id": idx,
        "scan_id": scan_id,
        "form_index": f.form_index,
        "field_name": f.field_name,
        "payload_index": f.payload.payload_id,
        "payload": f.payload.payload,
        "vuln_type": f.payload.vuln_type.name,
        "severity": f.payload.severity.name,
        "match_type": f.payload.match_type.name,
        "evidence": f.evidence,
        "response_time": f.response_time_ms,
        "body_length": f.body_len,
        "url": f.url,
    }


def export_findings(findings: List[Finding], scan_id: Optional[int]) -> list[dict]:
    """
    Возвращает находки в нормализованный формате.
    """
    normalized_findings = []
    for idx, f in enumerate(findings):
        try:
            nf = normalize_finding(f, idx + 1, scan_id) # finding_id начинается с 1 (для удобствва чтения)
            normalized_findings.append(nf)
        except Exception as e:
            logger.warning(
                "Skipping invalid finding during normalization",
                extra={"idx": idx, "error": str(e)},
            )
            continue
    logger.info(
        "Findings normalized",
        extra={"count": len(normalized_findings), "scan_id": scan_id},
    )
    return normalized_findings


def sample_findings(
    findings: list[dict], n: int = 3, stratify: bool = True
) -> list[dict]:
    """
    Возвращает выборку из n первых находок.
    """
    if not findings:
        return []
    return findings[:min(n, len(findings))]
