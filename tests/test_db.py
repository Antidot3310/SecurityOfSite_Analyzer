import os
import sys
import json
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.storage.db import init_db, save_scan, get_scan, db_connect


def test_init_db_and_save_get(tmp_path):
    dbpath = str(tmp_path / "t.db")
    init_db(dbpath)
    scan_id = save_scan(
        "http://ex",
        json.dumps({"forms": []}),
        {"count": 1, "status_code": 200, "response_size": 10},
        dbpath,
    )
    rec = get_scan(scan_id, dbpath)
    assert rec is not None
    assert rec["target"] == "http://ex"
    assert rec["count"] == 1
    assert rec["status_code"] == 200
    assert json.loads(rec["results_json"]) == {"forms": []}


def test_db_connect_and_transaction(tmp_path):
    dbfile = str(tmp_path / "t2.db")
    with db_connect(dbfile) as cur:
        cur.execute("CREATE TABLE demo (id INTEGER PRIMARY KEY, v TEXT)")
        cur.execute("INSERT INTO demo (v) VALUES (?)", ("a",))
    conn = sqlite3.connect(dbfile)
    cur = conn.cursor()
    cur.execute("SELECT v FROM demo")
    row = cur.fetchone()
    conn.close()
    assert row[0] == "a"
