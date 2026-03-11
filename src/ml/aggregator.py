"""
Модуль кластеризации находок на основе текстовых описаний.

Предоставляет функционал для группировки схожих находок по их payload
и evidence с использованием эмбеддингов.

Функции:
    prepare_and_cluster() - основная функция кластеризации находок.
"""

from collections import defaultdict, Counter
from typing import Iterable, List, Dict, Any, Optional
from functools import lru_cache

import hdbscan
import numpy as np
from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """Возвращает кэшированную модель SentenceTransformer для получения эмбеддингов."""
    return SentenceTransformer("all-MiniLM-L6-v2")


def get_payload_str(record: Dict[str, Any]) -> str:
    """Извлекает строковое представление payload из записи."""
    return record["payload"]["payload"]


def get_evidence(record: Dict[str, Any]) -> Optional[str]:
    """Извлекает evidence из записи находки."""
    return record.get("evidence")


def representative(records: List[Dict]) -> Dict:
    """
    Возвращает:
        Запись, содержащую наиболее часто встречающийся payload.
    """
    if not records:
        return {}
    payload_counts = Counter(get_payload_str(r) for r in records)
    most_common_payload, _ = payload_counts.most_common(1)[0]
    # Ищем первую запись с этим payload
    return next(r for r in records if get_payload_str(r) == most_common_payload)


def build_cluster(label: int, records: List[Dict]) -> Dict:
    """
    Формирует описание кластера на основе группы записей.

    Параметры:
        label: Метка кластера (число).
        records: Список записей, входящих в кластер.

    Возвращает:
        Словарь с полями:
            cluster_label : метка кластера
            findings_count : количество находок в кластере
            representative_payload : payload репрезентативной записи
            representative_evidence : evidence репрезентативной записи
    """
    rep = representative(records)
    return {
        "cluster_label": label,
        "findings_count": len(records),
        "representative_payload": get_payload_str(rep) if rep else None,
        "representative_evidence": rep.get("evidence") if rep else None,
    }


def embed_texts(texts: Iterable[str]) -> np.ndarray:
    """Преобразует коллекцию текстов в эмбеддинги с помощью SentenceTransformer."""
    model = get_model()
    # Преобразуем в список, чтобы избежать проблем с повторным проходом
    text_list = list(texts)
    return model.encode(text_list, show_progress_bar=False)


def cluster_embeddings(embeddings: np.ndarray) -> List[int]:
    """Выполняет кластеризацию эмбеддингов с использованием HDBSCAN."""
    clusterer = hdbscan.HDBSCAN(min_cluster_size=2, metric="euclidean")
    return clusterer.fit_predict(embeddings).tolist()


def prepare_and_cluster(findings: List[Dict]) -> Dict:
    """
    Основная функция кластеризации находок по текстовым описаниям.
    Параметры:
        findings: Список словарей с данными находок.

    Возвращает:
        Словарь с ключом 'clusters', содержащим список описаний кластеров.
    """
    if not findings:
        return {"clusters": []}

    texts = []
    for f in findings:
        payload = get_payload_str(f)
        evidence = get_evidence(f) or ""
        texts.append(f"{payload} {evidence}")

    embeddings = embed_texts(texts)
    labels = cluster_embeddings(embeddings)

    groups = defaultdict(list)
    for label, finding in zip(labels, findings):
        groups[label].append(finding)

    clusters = [build_cluster(label, recs) for label, recs in groups.items()]
    clusters.sort(key=lambda x: x["findings_count"], reverse=True)

    return {
        "clusters": clusters,
    }
