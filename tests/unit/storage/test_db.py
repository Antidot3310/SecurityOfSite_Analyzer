import json
from src.storage.db import init_db, save_scan, get_scan, db_connect


def test_save_and_get_scan(tmp_path):
    """Проверка сохранения и извлечения записи скана."""
    db_path = tmp_path / "scans.db"
    init_db(str(db_path))
    target = "http://example.com"
    results = {"forms": [{"action": "/login"}]}
    results_json = json.dumps(results)
    meta = {"count": 2, "status_code": 200, "response_size": 512}
    scan_id = save_scan(target, results_json, meta, str(db_path))

    record = get_scan(scan_id, str(db_path))
    assert record is not None
    assert record["target"] == target
    assert record["count"] == 2
    assert record["status_code"] == 200
    assert record["response_size"] == 512
    assert json.loads(record["results_json"]) == results


def test_save_scan_without_meta(tmp_path):
    db_path = tmp_path / "no_meta.db"
    init_db(str(db_path))
    scan_id = save_scan("http://test", json.dumps({}), path=str(db_path))
    record = get_scan(scan_id, str(db_path))
    assert record is not None
    assert record["count"] is None
    assert record["status_code"] is None
    assert record["response_size"] is None


def test_get_nonexistent_scan(tmp_path):
    """Проверка, что get_scan возвращает None для отсутствующего ID."""
    db_path = tmp_path / "empty.db"
    init_db(str(db_path))
    assert get_scan(999999, str(db_path)) is None
