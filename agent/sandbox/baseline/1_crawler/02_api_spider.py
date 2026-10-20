import os
import time
import random
from curl_cffi import requests

BASE_URL = "https://batdongsan.com.vn/ban-can-ho-chung-cu-tp-ho-chi-minh/p{page}?cIds=650,362,41,325,163,575,361,40,283,44,562,45,48&vrs=1"

def fetch_page_html(page: int, cookie_str: str) -> tuple[str, dict]:
    """Gửi HTTP request giả lập browser qua curl_cffi tải HTML trang danh sách."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Cookie": cookie_str
    }
    try:
        resp = requests.get(BASE_URL.format(page=page), headers=headers, impersonate="chrome120", timeout=15)
        if resp.status_code == 200:
            return resp.text, {"page": page, "status_code": 200, "bytes": len(resp.text)}
        return "", {"page": page, "status_code": resp.status_code, "error": resp.text[:100]}
    except Exception as e:
        return "", {"page": page, "status_code": 500, "error": str(e)}

if __name__ == "__main__":
    html, meta = fetch_page_html(1, "")
    print("Fetch page 1:", meta)
