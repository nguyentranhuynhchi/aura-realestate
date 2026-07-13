import time
import random
import os
import csv
import re
from curl_cffi import requests 
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

OUTPUT_CSV = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "new_data.csv"))

BASE_URL = "https://batdongsan.com.vn/ban-can-ho-chung-cu-tp-ho-chi-minh/p{page}?cIds=650,362,41,325,163,575,361,40,283,44,562,45,48&vrs=1"

def get_fresh_cookie():
    """Hàm bật trình duyệt ảo ngầm để lấy Cookie tươi mới hoàn toàn tự động"""
    print("[PLAYWRIGHT] Đang kích hoạt trình duyệt ẩn để bốc Cookie tự động...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True) # headless=True để chạy ẩn không tốn RAM
            context = browser.new_context()
            page = context.new_page()
            
            # Truy cập trang chủ để kích hoạt cấp session/cookie mới
            page.goto("https://batdongsan.com.vn", wait_until="networkidle", timeout=20000)
            
            cookies = context.cookies()
            cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies if ord(c['name']) < 128 and ord(c['value']) < 128])
            
            browser.close()
            print("[SUCCESS] Đã bốc Cookie tự động thành công từ Playwright!")
            return cookie_string
    except Exception as e:
        print(f"[WARNING] Playwright không lấy được cookie: {e}. Hệ thống sẽ chạy không có cookie.")
        return ""

FIELDNAMES = [
    "id", "title", "price_raw", "area_raw", "address_raw", "url", "seller_name", 
    "phone_number", "bedrooms", "bathrooms", "floors", "house_direction", 
    "legal_status", "interior", "ownership_type", "price_trend", "description", "surrounding_area"
]

def clean_text(text):
    if not text: return "N/A"
    return text.replace("\n", " ").replace("\r", " ").strip().replace('"', "'")

def sanitize_cookie(cookie_string):
    return "".join([c for c in cookie_string if ord(c) < 128])

def extract_phone_from_text(text):
    if not text or text == "N/A": return "N/A"
    pattern = r'(03|05|07|08|09|01[2689])([ ._-]*\d){8}\b'
    match = re.search(pattern, text)
    if match:
        phone = match.group(0)
        return re.sub(r'[-. ]', '', phone)
    return "N/A"

def scrape_v3(start_page, end_page):
    print(f"\nChạy từ trang {start_page} đến trang {end_page}")
    
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    file_exists = os.path.isfile(OUTPUT_CSV)
    
    clean_cookie = get_fresh_cookie()
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "cookie": clean_cookie,
        "referer": "https://batdongsan.com.vn/"
    }

    sample_count = 0

    with open(OUTPUT_CSV, mode='a', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()

        for page in range(start_page, end_page + 1):
            url = BASE_URL.format(page=page)
            print(f"[Khai thác phân đoạn] Đang quét danh sách trang [{page}/{end_page}]")
            
            try:
                res = requests.get(url, headers=headers, impersonate="chrome120", timeout=15, max_redirects=5)
                if res.status_code != 200:
                    print(f"Bị Cloudflare chặn tại trang tổng {page}. Mã: {res.status_code}")
                    continue
                
                soup = BeautifulSoup(res.text, "html.parser")
                cards = soup.select("div.js__card-listing") or soup.select("div[class*='re__card-full']")
                
                for item in cards:
                    try:
                        uid = item.get("uid") or item.get("data-product-id") or item.get("id")
                        if not uid: continue
                        
                        link_el = item.select_one("a.js__product-link-for-product-id") or item.select_one("a")
                        house_url = f"https://batdongsan.com.vn{link_el.get('href')}" if link_el and link_el.get('href') else ""
                        if not house_url.startswith("https://"): continue
                        
                        title_el = item.select_one("h3.re__card-title")
                        price_el = item.select_one("span.re__card-config-price")
                        area_el = item.select_one("span.re__card-config-area")
                        loc_el = item.select_one("div.re__card-location")
                        
                        house_data = {
                            "id": clean_text(uid), "title": clean_text(title_el.text) if title_el else "N/A",
                            "price_raw": clean_text(price_el.text) if price_el else "N/A",
                            "area_raw": clean_text(area_el.text) if area_el else "N/A",
                            "address_raw": clean_text(loc_el.text) if loc_el else "N/A", "url": house_url, 
                            "seller_name": "N/A", "phone_number": "N/A", "bedrooms": "N/A", "bathrooms": "N/A", 
                            "floors": "N/A", "house_direction": "N/A", "legal_status": "N/A", "interior": "N/A", 
                            "ownership_type": "N/A", "price_trend": "N/A", "description": "N/A", "surrounding_area": "N/A"
                        }

                        res_detail = requests.get(house_url, headers=headers, impersonate="chrome120", timeout=15, max_redirects=5)
                        if res_detail.status_code == 200:
                            soup_detail = BeautifulSoup(res_detail.text, "html.parser")
                            
                            addr_el = soup_detail.select_one(".re__pr-address") or soup_detail.select_one("span.re__pr-short-info-item_title")
                            if addr_el: house_data["address_raw"] = clean_text(addr_el.text.replace("Địa chỉ:", "").strip())
                            elif house_data["address_raw"] != "N/A" and house_data["address_raw"].startswith("·"):
                                house_data["address_raw"] = clean_text(house_data["address_raw"].replace("·", "").strip())

                            desc_el = soup_detail.select_one("div.re__section-body.re__detail-content") or soup_detail.select_one(".re__pr-description")
                            if desc_el: house_data["description"] = clean_text(desc_el.text)

                            phone_el = soup_detail.select_one(".re__contact-phone") or soup_detail.select_one(".js__phone")
                            raw_phone = phone_el.get("data-phone") if phone_el else ""
                            if raw_phone and "***" not in raw_phone: house_data["phone_number"] = clean_text(raw_phone)
                            else: house_data["phone_number"] = extract_phone_from_text(house_data["description"])

                            seller_el = soup_detail.select_one("div.re__contact-name") or soup_detail.select_one(".js__contact-name")
                            if seller_el: house_data["seller_name"] = clean_text(seller_el.get("title") or seller_el.text)

                            trend_container = soup_detail.select_one(".re__market-prices-chart-summary")
                            if trend_container:
                                val_el = trend_container.select_one(".re__market-prices-chart-summary-value")
                                lbl_el = trend_container.select_one(".re__market-prices-chart-summary-label")
                                if val_el and lbl_el: house_data["price_trend"] = clean_text(f"{val_el.text} - {lbl_el.text}")

                            surround_el = soup_detail.select_one(".re__surrounding-facilities") or soup_detail.select_one(".js__location-surrounding")
                            if surround_el: house_data["surrounding_area"] = clean_text(surround_el.text)

                            specs = soup_detail.select("div.re__pr-specs-content-item") or soup_detail.select(".re__pr-specs-content-v2 div")
                            for spec in specs:
                                title = spec.select_one("[class*='title']") or spec.select_one("span")
                                value = spec.select_one("[class*='value']") or spec.select_one("strong")
                                if title and value:
                                    t_text = title.text.strip().lower()
                                    v_text = value.text.strip()
                                    if "phòng ngủ" in t_text: house_data["bedrooms"] = v_text
                                    elif "phòng tắm" in t_text or "toilet" in t_text: house_data["bathrooms"] = v_text
                                    elif "số tầng" in t_text: house_data["floors"] = v_text
                                    elif "hướng nhà" in t_text: house_data["house_direction"] = v_text
                                    elif "pháp lý" in t_text: house_data["legal_status"] = v_text
                                    elif "nội thất" in t_text: house_data["interior"] = v_text
                                    elif "loại hình" in t_text or "sở hữu" in t_text: house_data["ownership_type"] = v_text

                        writer.writerow(house_data)
                        f.flush()
                        sample_count += 1
                        print(f"Đã ghi trực tiếp căn nhà số {sample_count} (ID: {house_data['id']})")

                    except Exception: continue
                    time.sleep(random.uniform(2.5, 3.8))

            except Exception as e:
                print(f"Lỗi kết nối trang tổng {page}: {e}")
            time.sleep(1)

    print(f"Hoàn thành phân đoạn. Đã ghi nối đuôi thành công {sample_count} mẫu dữ liệu.")
    return []