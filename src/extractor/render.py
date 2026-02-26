from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout


def render_html_with_playwright(url: str, timeout: int = 8000) -> str | None:
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=timeout, wait_until="networkidle")
            page.wait_for_timeout(300)
            html = page.content()
            browser.close()
            return html
    except PWTimeout:
        return None
    except Exception:
        return None
