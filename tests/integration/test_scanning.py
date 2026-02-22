import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def test_demo_integration(tmp_path, monkeypatch):
    """
    Линия тестирования:
    - создать html с одной формой (name=q)
    - распарсить форму при помощи extract_forms
    - monkeypatch send_form_request:
        baseline -> returns clean snapshot
        запрлсы где q == payload.payload -> возвращает инжектированный снапшот
    - запустить scan_forms
    """
    # local imports
    from src.extractor.extractor import extract_forms
    from src.scanner.scanner import scan_forms, ResponseSnapshot
    from src.scanner.types import Payload, VulnType, Severity, MatchType

    html = """
    <!doctype html>
    <html>
      <body>
        <form id="demo" action="http://example/submit" method="get">
          <input name="q" value="">
          <input type="submit" value="Send">
        </form>
      </body>
    </html>
    """
    # записываем во временный файл
    p = tmp_path / "page_demo.html"
    p.write_text(html, encoding="utf-8")

    # парсим формы
    forms = extract_forms(html, url="https://example.com")
    assert len(forms) >= 1
    form = forms[0].to_dict()

    payload = Payload(
        payload_id="xss-demo",
        payload="<script>alert(1)</script>",
        vuln_type=VulnType.XSS,
        severity=Severity.MEDIUM,
        match_type=MatchType.REFLECTED,
        evidence_patterns=[],
    )
    payloads = [payload]

    # base и injected снапшоты
    base_snap = ResponseSnapshot(
        url="http://example/submit",
        status_code=200,
        body="Hello",
        body_len=5,
        response_time=100,
    )
    inj_body = f"some page content... {payload.payload} ...rest"
    inj_snap = ResponseSnapshot(
        url="http://example/submit?q=%3Cscript%3Ealert(1)%3C%2Fscript%3E",
        status_code=200,
        body=inj_body,
        body_len=len(inj_body),
        response_time=150,
    )

    # подменяем отправку запросов (base без payload, injected с ним)
    def fake_send_form_request(form_arg, data_arg, timeout=8, session=None):
        if not data_arg:
            return base_snap
        for v in data_arg.values():
            if v == payload.payload:
                return inj_snap
        return base_snap

    monkeypatch.setattr("src.scanner.scanner.send_form_request", fake_send_form_request)

    # сканируем формы
    findings = scan_forms([form], payloads, rate_limit=0)

    assert isinstance(findings, list)
    assert len(findings) >= 1
    found = False
    for f in findings:
        if f.field_name == "q" or getattr(f, "field_name", "") == "q":
            assert "alert" in f.evidence.lower()
            found = True
    assert found
