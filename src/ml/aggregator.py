from collections import defaultdict, Counter
from typing import Iterable, List, Dict, Any

import hdbscan
import numpy as np
from sentence_transformers import SentenceTransformer
from functools import lru_cache


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer("all-MiniLM-L6-v2")


def get_payload_str(record: Dict[str, Any]) -> str:
    return record["payload"]["payload"]


def get_evidence(record: Dict[str, Any]) -> str:
    return record.get("evidence")


def representative(records: List[Dict]) -> Dict:
    """Запись с самым частым payload."""
    if not records:
        return {}
    payload_counts = Counter(get_payload_str(r) for r in records)
    most_common_payload, _ = payload_counts.most_common(1)[0]
    return next(r for r in records if get_payload_str(r) == most_common_payload)


def build_cluster(label: int, records: List[Dict]) -> Dict:
    """Описание кластера."""
    rep = representative(records)
    return {
        "cluster_label": label,
        "findings_count": len(records),
        "representative_payload": get_payload_str(rep),
        "representative_evidence": rep.get("evidence"),
    }


def embed_texts(texts: Iterable[str]) -> np.ndarray:
    """Кодирование текстов в эмбеддинги."""
    model = get_model()
    return model.encode(list(texts), show_progress_bar=False)


def cluster_embeddings(embeddings: np.ndarray) -> List[int]:
    """Кластеризация эмбеддингов."""
    clusterer = hdbscan.HDBSCAN(min_cluster_size=2, metric="euclidean")
    return clusterer.fit_predict(embeddings).tolist()


def prepare_and_cluster(findings: List[Dict]) -> Dict:
    """
    Кластеризация находок по текстовым описаниям.
    Возвращает словарь с кластерами и общим количеством находок.
    """
    if not findings:
        return {"clusters": [], "findings_count": 0}

    texts = [get_payload_str(f) + " " + get_evidence(f) for f in findings]

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
