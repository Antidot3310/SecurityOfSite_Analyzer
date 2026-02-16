@echo off
call D:/Project/venv/Scripts/activate.bat

curl "http://127.0.0.1:5000/api/scan?url=file:///D:/Project/tests/test_data/page_sqli.html" > demo_scan.json
python -m json.tool demo_scan.json
pause