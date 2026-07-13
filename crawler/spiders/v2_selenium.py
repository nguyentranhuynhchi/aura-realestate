import time
import random
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth

BASE_URL = "https://batdongsan.com.vn/ban-nha-dat-tp-hcm/p{page}"

def scrape_v2(max_pages):
    print("[->] Đang thực thi Bản nâng cao (Selenium Stealth Toàn Diện)...")
    results = []
    
    # 1. Cau hinh Options tieu chuan, khong dung cac co gay crash luong
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Loai bo cac dau vet tu dong hoa mac dinh
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 2. Khoi tao Driver phu hop voi may em
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # 3. Kich hoat che do Stealth (Gia lap nguoi dung that cap do cao)
    stealth(driver,
        languages=["vi-VN", "vi", "en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    
    try:
        for page in range(1, max_pages + 1):
            url = BASE_URL.format(page=page)
            try:
                print(f"[+] Bot đang điều hướng tới: {url}")
                driver.get(url)
                
                # ÉP BẮT BUỘC DỪNG LẠI Ở MỌI TRANG để em kiểm tra xem có bị Cloudflare chặn không
                print(f"\n[!] BẮT BUỘC: Em nhìn màn hình Chrome Trang {page}. Nếu có ô Cloudflare thì tích vào.")
                input(f"[*] ĐỢI WEB TẢI XONG DANH SÁCH TRANG {page} -> Quay lại gõ ENTER để cào... ")
                
                # CƠ CHẾ CUỘN TRANG: Giả lập người dùng cuộn chuột xuống từ từ để web render hết class ẩn
                print("[*] Đang giả lập cuộn trang để kích hoạt tải dữ liệu...")
                for i in range(1, 5):
                    driver.execute_script(f"window.scrollTo(0, {i * 800});")
                    time.sleep(0.8)
                
                # Quét tin đăng bằng CSS Selector
                cards = driver.find_elements(By.CSS_SELECTOR, "div.js__card-listing")
                print(f"[*] Trang {page}: Tìm thấy {len(cards)} thẻ tin đăng.")
                
                for item in cards:
                    try:
                        uid = item.get_attribute("uid")
                        vip_type = item.get_attribute("vtp")
                        
                        if not uid:
                            continue
                        
                        link_element = item.find_element(By.CSS_SELECTOR, "a.js__product-link-for-product-id")
                        house_url = link_element.get_attribute("href")
                        
                        try:
                            title_text = item.find_element(By.CSS_SELECTOR, "span.re__card-title").text
                            price_text = item.find_element(By.CSS_SELECTOR, "span.re__card-price").text
                            area_text = item.find_element(By.CSS_SELECTOR, "span.re__card-acreage").text
                            location_text = item.find_element(By.CSS_SELECTOR, "div.re__card-location").text
                        except Exception:
                            info_element = item.find_element(By.CSS_SELECTOR, "div.re__card-info")
                            title_text = info_element.get_attribute("title")
                            price_text, area_text, location_text = "Check title", "Check title", "Check title"

                        try:
                            desc_element = item.find_element(By.CSS_SELECTOR, "div.re__card-description")
                            short_description = desc_element.text
                        except Exception:
                            short_description = ""

                        try:
                            trend_element = item.find_element(By.CSS_SELECTOR, "span.re__card-price-trend")
                            price_trend = trend_element.text
                        except Exception:
                            price_trend = "0%"

                        try:
                            date_element = item.find_element(By.CSS_SELECTOR, "span.re__card-published-date")
                            published_date = date_element.get_attribute("aria-label") or date_element.text
                        except Exception:
                            published_date = "Unknown"

                        try:
                            img_element = item.find_element(By.CSS_SELECTOR, "div.re__card-image img")
                            image_url = img_element.get_attribute("src") or img_element.get_attribute("data-src")
                        except Exception:
                            image_url = "No Image"

                        results.append({
                            "id": uid.strip(),
                            "title": title_text.strip() if title_text else "",
                            "price_raw": price_text.strip() if price_text else "", 
                            "area_raw": area_text.strip() if area_text else "",
                            "address_raw": location_text.strip() if location_text else "",
                            "short_description": short_description.strip() if short_description else "",
                            "url": house_url,
                            "vip_type": vip_type,
                            "price_trend": price_trend.strip(),
                            "image_url": image_url,
                            "published_date": published_date.strip() if published_date else "",
                            "target_price": "", "bedrooms": "", "bathrooms": "", "floors": "",
                            "house_direction": "", "balcony_direction": "", "entrance_width": "",
                            "legal_status": "", "interior": "", "phone_number": ""
                        })
                    except Exception:
                        continue
                        
            except Exception as e:
                print(f"[!] Lỗi tại trang {page}: {e}")
                
            # Nghỉ ngơi ngẫu nhiên để tránh bị phát hiện thuật toán
            time.sleep(random.uniform(3.0, 6.0))
            
    finally:
        if 'driver' in locals() and driver:
            try:
                driver.quit()
            except Exception:
                pass
        print("[*] Đã dọn dẹp tiến trình trình duyệt an toàn.")
        
    return results