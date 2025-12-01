import sys
import os
import json
import pytest

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

from src.storage.db import init_db, save_scan, get_scan    

def test_database_save_and_load(tmp_path):
    dbpath = tmp_path / "test_db.db"
    init_db(str(dbpath))
    scan_id = save_scan(path = str(dbpath), target="example.com", results_json=json.dumps({"key" : "15"}), meta={"count": 10, "status_code": 200, "response_size": 512})
    result = get_scan(path= str(dbpath), scan_id= scan_id)
    assert result is not None
    assert result["target"] == "example.com"
    assert result["count"] == 10
    assert result["status_code"] == 200
    assert result["response_size"] == 512
    assert json.loads(result["results_json"]) == {"key" : "15"}



