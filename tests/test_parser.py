import os
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root not in sys.path:
    sys.path.insert(0, root)
from src.parser import fetch_info


def test_fetch_info_local_ok():
    res = fetch_info(url="file://./tests/local.html", timeout=4)
    print(res)
    assert res["ok"] == True


def test_fetch_info_local_not_found():
    res = fetch_info(url="file://./not/existing/file", timeout=4)
    assert res["ok"] == False
    assert res["error"] == "File not found"
