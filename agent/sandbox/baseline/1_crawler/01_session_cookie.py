from playwright.sync_api import sync_playwright

def get_fresh_cookie() -> tuple[str, dict]:
    """Khởi tạo trình duyệt ẩn danh Playwright để bốc cookie phiên tươi mới."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://batdongsan.com.vn", wait_until="networkidle", timeout=20000)
            cookies = page.context.cookies()
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies if ord(c['name']) < 128 and ord(c['value']) < 128])
            browser.close()
            return cookie_str, {"status": "success", "cookie_len": len(cookie_str)}
    except Exception as e:
        return "", {"status": "warning", "message": str(e)}

if __name__ == "__main__":
    cookie, meta = get_fresh_cookie()
    print("Metadata:", meta)
