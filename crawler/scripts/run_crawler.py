import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from spiders.v3_api_hidden import scrape_v3

def main():
    version = "v3"
    
    start_page = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    end_page = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    
    print(f"[Kích hoạt AURA Crawler Cluster - Phiên bản: {version.upper()}")
    print(f"Tiến trình xử lý phân đoạn: Từ Trang {start_page} đến Trang {end_page}")
    
    if version == "v3":
        scrape_v3(start_page, end_page)
    else:
        print(f"Cấu hình phiên bản '{version}' không hợp lệ.")

if __name__ == "__main__":
    main()