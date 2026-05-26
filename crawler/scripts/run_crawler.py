import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from spiders.v3_api_hidden import scrape_v3
from spiders.v1_api_hidden import scrape_v1
from spiders.v2_api_hidden import scrape_v2

def main():
    version = sys.argv[1] if len(sys.argv) > 1 else "v3"
    
    start_page = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    end_page = int(sys.argv[3]) if len(sys.argv) > 3 else 44
    
    print(f"[Kích hoạt AURA Crawler Cluster - Phiên bản: {version.upper()}")
    print(f"Tiến trình xử lý phân đoạn: Từ Trang {start_page} đến Trang {end_page}")
    
    if version == "v3":
        scrape_v3(start_page, end_page)
    elif version == "v1":
        scrape_v1(end_page)
    elif version == "v2":
        scrape_v2(end_page)
    else:
        print(f"Cấu hình phiên bản '{version}' không hợp lệ.")

if __name__ == "__main__":
    main()