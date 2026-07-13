# Bản cơ bản (Requests + BS4 - Tốc độ nhanh nhất)
import time
import random
import requests
from bs4 import BeautifulSoup
import os

BASE_URL = "https://batdongsan.com.vn/ban-nha-tp-hcm/p{page}"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]

def scrape_v1(max_pages):
    print("[->] Đang thực thi Bản cơ bản (Requests + BS4)...")
    results = []
    
    for page in range(1, max_pages + 1):
        url = BASE_URL.format(page=page)
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
           
            debug_dir = os.path.dirname(os.path.abspath(__file__))
            with open(os.path.join(debug_dir, "debug_page.html"), "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"[*] Đã đọc HTML thô về file: crawler/spiders/debug_page.html")

            if response.status_code != 200:
                continue
                
            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.find_all("div", class_="js__card")
            
            for item in cards:
                try:
                    results.append({
                        "title": item.find("span", class_="re__card-title").text.strip(),
                        "price_raw": item.find("span", class_="re__card-price").text.strip(),
                        "area_raw": item.find("span", class_="re__card-acreage").text.strip(),
                        "address": item.find("div", class_="re__card-location").text.strip()
                    })
                except Exception:
                    continue
        except Exception as e:
            print(f"[!] Lỗi kết nối v1 tại trang {page}: {e}")
            
        time.sleep(random.uniform(1.5, 3.0))
    return results