import time
import random
import os
import csv
import re
from curl_cffi import requests 
from bs4 import BeautifulSoup

OUTPUT_CSV = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "houses_raw.csv"))

BASE_URL = "https://batdongsan.com.vn/ban-can-ho-chung-cu-tp-ho-chi-minh/p{page}?cIds=650,362,41,325,163,575,361,40,283,44,562,45,48&vrs=1"

COOKIE_STR = (
    "_gcl_au=1.1.1992001346.1779449118; _ga=GA1.1.1237519992.1779449119; __uidac=016a103d1fa3363e915f0765a11bab37; "
    "__admUTMtime=1779449119; _fbp=fb.2.1779449119684.495652868306778629; _tt_enable_cookie=1; _ttp=01KS7PXHQF5TCXK4ENSNG4XR1G_.tt.2; "
    "__iid=6461; __iid=6461; __su=0; __su=0; __RC=5; __R=3; "
    "_hjSessionUser_1708983=eyJpZCI6ImNhZGNlZGViLWFlZWMtNTZkNy1hYjFhLWEwZGUwNWVkNGRiOCIsImNyZWF0ZWQiOjE3Nzk0NDkxMTkxNDEsImV4aXN0aW5nIjp0cnVlfQ==; "
    "__tb=0; ajs_anonymous_id=7b58b2db-2982-41ed-b388-359478a0dba1; userinfo=4c0906ae13b14a369d20a7e99a1133aa@bds.lc; c_u_id=5195219; "
    "BDS.UMS.Cookie=CfDJ8GsOAEqwP6xPtxb1UfIzE281cgGmTyFu522mq1HGUt-9tyToBhM-tIiwuHK0_hAtrY0xmnVgXHprrJnrHh-r8BA1sRFYRgOifJPdRhLlJNiz3JzcZr-NhYZyXe0loWV7TSg7961cGtXRIzGV1Md_72fu7fySg64HQs2m3lB72K-Gp-gh-GBY9Lyjk1NMZvNlc3k90VuVuOPfGAxTdI4K7HUg3l20ZDLJ-ceiQUH7YMo5ZobmFjQOi9u9n4E_qnwxjIJcYAcgcxTUZWJlFE-8ZOtLwEgtsAhj1kW2IuPYXMfDhoOR1rXPQSXI9BIOq-PP25aIPyIAZxrwWFCylBozSZXvyhvhF1H2fVX0lxkSetWn1YSVaTpDgnTyWloaZEKkc8--WsKVaKXRHU0qwuRlUxhLEQ74W39xu2PO60o08t3VMbmBIAIbcHJ2Baac6Ry73GpcgflaFLKomK7GZZKhiUo-njk8LEUTeGvN8Q8Pw220YU4cS9MEpJE7BD0X-LTz0p3QyS80pizlZDJ5hyt0PuweAPNh6WYjUGQp6Y0HlwhHA35mTC4E_UOukEyvknqjxHJi8mC7d_5uX3bgd6UGPGjjfUO6tgFJtOr6d-Ix2WbNG9G-axNsqdeym6TdZLShkPK6qJfgGuHXrE93qMoeI-0xNvdhzx55PWPF7gYH-OHzxf_RCF9cc4ewqu_rUGnsrw; "
    "ajs_user_id=5195219; clientIp=2001%3Aee0%3A4f0c%3A2070%3Ae2%3A4a59%3A66ed%3Add5b; con.unl.lat=1779555600; con.unl.sc=3; __IP=0; "
    "con.ses.id=06381f08-a6b0-432e-b9c5-4e878c33e369; "
    "_cfuvid=6xZOTlUHR31nlVn4R44hG0YPM3DjDoOC8rL6es2puWc-1779610535.265167-1.0.1.1-w3TMuHOmzJs5A2d6HrCMAUveE1AzwgJoaxHtFvxI6n8; "
    "refreshToken=oqWCkpJjExuKJW6HESokZkcg8JzVHNXhRFeJa4cMBJ8; "
    "accessToken=eyJhbGciOiJSUzI1NiIsImtpZCI6Ijg5Mzg0OTU1MkNDRTExMUFDMjc5RjUyNDI3RUEwMUY5QzdDMzAxNTQiLCJ0eXAiOiJhdCtqd3QiLCJ4NXQiOiJpVGhKVlN6T0VSckNlZlVrSi1vQi1jZkRBVlEifQ.eyJuYmYiOjE3Nzk2MTA1MzUsImV4cCI6MTc3OTYxNDEzNSwiaXNzIjoiaHR0cDovL2F1dGhlbnRpY2F0aW9uLmJkcy5sYyIsImF1ZCI6IkFwaUdhdGV3YXkiLCJjbGllbnRfaWQiOiIwM2QwZjkwNS0xMGM5LTRkMjEtOTBmNS0xMGI3OGUwYTk4OWMiLCJzdWIiOiI1MTk1MjE5IiwiYXV0aF90aW1lIjoxNzc5NTcyMjExLCJpZHAiOiJsb2NhbCIsInByZWZlcnJlZF91c2VybmFtZSI6IjAzMzk3MzcyNzUiLCJlbWFpbCI6IjRjMDkwNmFlMTNiMTRhMzY5ZDIwYTdlOTlhMTEzM2FhQGJkcy5sYyIsInNjb3BlIjpbIm9wZW5pZCIsInByb2ZpbGUiLCJBcGlHYXRld2F5Iiwib2ZmbGluZV9hY2Nlc3MiXSwiYW1yIjpbInB3ZCJdfQ.QHd08SydFjRfpMJfhrk7uUlnt4CalOleWs1KOy9sV-jCkF0iFl4_KVw4lrtlLgEbUN0VnlF3VAC5HOlpSnEKrFQyXL2VKoarMMxPaySs_Y8feQmb-2AHKLKous5yw2ZVtFhWeHLPIGXKqELoMByHBVDG7ihNsl9pHL076182jU5UFgkg_4Xl1hn9IS3oNU31pawae8xDAvC0sZWMIcNZcx_UOzbZYrJ0A8ErKKTkUSdVS9lZJKqkvBsatrEHfAPni_Ras5VSQNG43h2MP1AI_xM4Q3sxYKewW04BX2OHFEFOb94y0K4q7F-9iX9DXtAIy6XkCSHp7w1Eed6kbGtOVA; "
    "cf_clearance=kAI9b_dXNU4mh26Luj8uBDSkS2y37v5inDpWrQEjYDc-1779610538-1.2.1.1-dZsYoa2_yVCn8LuD9ix1xLbaj_by2FoqMX6mHh6TBg6uJ28B839ROGm8bXeGZHrx28MD8iokjoZ8ucWg.tsTzdktQdzlyn24tOdfKI5_ln4.JYzV7xQcdBr353I1OmTr9Omqq_MlTKtstp1bU4mBI3TnfU4jwfoEq.lDD_XvqKYxKdiHtR5RrNGmVZrw.RbOFpcZPhJ7faq0olTkkS2DQpMftCuK2c.htXrfjycB97QXFAJwVE9nnkkKlpNsEdEHNJRp87gL4hUbcbk8HvXO_brmKUPtNrFEU8SdyWWMo1dIFuHORjyYvMoybyt0xyxcblz5Xu_dN35qo8lSnsYK0w; "
    "_hjSession_1708983=eyJpZCI6ImU4MDFlNGEwLWYyZDEtNGUzNC1hOTg0LWMxYzJkZDBlNjI0ZiIsImMiOjE3Nzk2MTA1MzgyMTMsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MX0=; "
    "_hjHasCachedUserAttributes=true; __gads=ID=21ff3e925794927f:T=1779449118:RT=1779610538:S=ALNI_MbEy5l5Bx6zxzcixJ1-nVVXN3-tKw; "
    "__gpi=UID=000014224ec1e44c:T=1779449118:RT=1779610538:S=ALNI_MaJXPhbuwoyDAlFKzUmooyJjaQAQw; __eoi=ID=b002f93955585dab:T=1779449118:RT=1779610538:S=AA-AfjZRoV9dtqQInoqo6mjP7rS-; "
    ".AspNetCore.Antiforgery.VyLW6ORzMgk=CfDJ8Anygllkf01LmPoxwxDcQG1PQDZV1rL34WOGDRnn9foznvO4lq3-m93uSGZbD6LXWdWJkcim-G_Y4HcXwwWVsEt9iUT3p-yn-lB2r4YncmZQSt-I4ZkU8Lo7uQHXF12HgqTemciMlTZCm7qgK2A4fZ4; "
    "ab.storage.deviceId.892f88ed-1831-42b9-becb-90a189ce90ad=%7B%22g%22%3A%22159e23a8-6670-7390-6d97-c03a28bfebb4%22%2C%22c%22%3A1779449121090%2C%22l%22%3A1779610541437%7D; "
    "ab.storage.userId.892f88ed-1831-42b9-becb-90a189ce90ad=%7B%22g%22%3A%225195219%22%2C%22c%22%3A1779547020730%2C%22l%22%3A1779610541438%7D; SEARCH_NEW_AND_OLD_ADDRESS=true; "
    "ab.storage.sessionId.892f88ed-1831-42b9-becb-90a189ce90ad=%7B%22g%22%3A%22b0f7c838-8f14-a33f-a65b-9aaa168d9dfd%22%2C%22e%22%3A1779612355932%2C%22c%22%3A1779610541435%2C%22l%22%3A1779610555932%7D; "
    "__uif=__uid%3A7694491193484553988%7C__ui%3A-1%7C__create%3A1779449120; "
    "AWSALB=heX47VkWfLRCVILZdMvtL5jhstA2Bq1Wzui+prqIk4U6iEzvPOxuxyTZ1VzCkV/Fh70q135piQWq2xamGp39OP3SWnTdi65ghvawC4mMSvesHM2W+iaG5Y7xBvJi; "
    "AWSALBCORS=heX47VkWfLRCVILZdMvtL5jhstA2Bq1Wzui+prqIk4U6iEzvPOxuxyTZ1VzCkV/Fh70q135piQWq2xamGp39OP3SWnTdi65ghvawC4mMSvesHM2W+iaG5Y7xBvJi; "
    "con.unl.usr.id=%7B%22key%22%3A%22userId%22%2C%22value%22%3A%227b58b2db-2982-41ed-b388-359478a0dba1%22%2C%22expireDate%22%3A%222027-05-24T15%3A15%3A56.7421101Z%22%7D; "
    "con.unl.cli.id=%7B%22key%22%3A%22clientId%22%2C%22value%22%3A%22a0ddb49d-794e-44bd-bc00-5773f1b00652%22%2C%22expireDate%22%3A%222027-05-24T15%3A15%3A56.7421302Z%22%7D; "
    "exp.stg.stableid=%7B%22key%22%3A%22stableID%22%2C%22value%22%3A%2259eed76b-b8f1-4eb1-9a98-6b4cc67278e2%22%2C%22expireDate%22%3A%222027-05-24T15%3A15%3A56.742253Z%22%7D; "
    "_ga_HTS298453C=GS2.1.s1779610537$o5$g1$t1779610556$j41$l0$h0$dpsWG8LySwmelmuMVWsEE60pF3ER1xz930Q; "
    "ttcsid=1779610538678::smzuGttOokCJyY5Cc26M.5.1779610563938.0::1.14937.16949::25253.10.315.9044::24366.21.8800; "
    "ttcsid_CHHL1E3C77U1H95PSJM0=1779610538677::A3QNTVsm_3uzScplJlD9.5.1779610563938.1; "
    "ph_phc_Twg4bLVDz7InVj8BSvMQBW4gX1KtsbnaOKWSdn0SupU_posthog=%7B%22%24device_id%22%3A%22019e4f6e-bd78-7930-a7e9-73145c6fc01e%22%2C%22distinct_id%22%3A%225195219%22%2C%22%24sesid%22%3A%5B1779610563955%2C%22019e590d-cd7a-7e1c-83fd-cde510178480%22%2C1779610537327%5D%2C%22%24epp%22%3Atrue%2C%22%24initial_person_info%22%3A%7B%22r%22%3A%22%24direct%22%2C%22u%22%3A%22https%3A%2F%2Fbatdongsan.com.vn%2F%22%7D%2C%22%24user_state%22%3A%22identified%22%7D"
)

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
    
    clean_cookie = sanitize_cookie(COOKIE_STR)
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