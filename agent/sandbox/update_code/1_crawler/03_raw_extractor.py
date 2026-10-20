import os
import csv
import re
from bs4 import BeautifulSoup

FIELDNAMES = [
    "id", "title", "price_raw", "area_raw", "address_raw", "url", "seller_name",
    "phone_number", "bedrooms", "bathrooms", "floors", "house_direction",
    "legal_status", "interior", "ownership_type", "price_trend", "description", "surrounding_area"
]

def clean_txt(t: str) -> str:
    return t.replace("\n", " ").replace("\r", " ").strip().replace('"', "'") if t else "N/A"

def parse_and_save_items(html_list: list[str], output_csv: str, max_limit: int = 50) -> tuple[int, dict]:
    """Bóc tách 18 trường thô từ HTML và lưu append vào file new_data.csv."""
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    file_exists = os.path.exists(output_csv)
    saved_count = 0

    with open(output_csv, mode="a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists or os.path.getsize(output_csv) == 0:
            writer.writeheader()

        for html in html_list:
            if not html or saved_count >= max_limit:
                break
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.find_all("div", class_=re.compile(r"js__card|re__card-info"))
            for card in cards:
                if saved_count >= max_limit:
                    break
                title_tag = card.find(["h3", "span"], class_=re.compile(r"re__card-title|title"))
                title = clean_txt(title_tag.get_text()) if title_tag else "N/A"
                price_tag = card.find("span", class_=re.compile(r"price"))
                price = clean_txt(price_tag.get_text()) if price_tag else "N/A"
                area_tag = card.find("span", class_=re.compile(r"area"))
                area = clean_txt(area_tag.get_text()) if area_tag else "N/A"
                addr_tag = card.find("span", class_=re.compile(r"location|address"))
                addr = clean_txt(addr_tag.get_text()) if addr_tag else "N/A"
                url_tag = card.find("a", href=True)
                url = url_tag["href"] if url_tag else "N/A"

                item = {k: "N/A" for k in FIELDNAMES}
                item.update({
                    "id": str(abs(hash(url or title)))[:10],
                    "title": title, "price_raw": price, "area_raw": area,
                    "address_raw": addr, "url": url
                })
                writer.writerow(item)
                saved_count += 1

    return saved_count, {"extracted_items": saved_count, "output_file": output_csv}

if __name__ == "__main__":
    print("Extractor module initialized.")
