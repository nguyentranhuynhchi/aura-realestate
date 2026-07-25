import schedule
import time
import subprocess
import sys
from datetime import datetime

def trigger_pipeline():
    """Hàm tự động gọi file run_pipeline.py giống như khi gõ lệnh thủ công"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{current_time}] ĐÚNG GIỜ HẸN! Đang kích hoạt Aura MLOps Pipeline...")
    
    try:
        result = subprocess.run([sys.executable, "run_pipeline.py"], check=True)
        print(f" [{datetime.now().strftime('%H:%M:%S')}] Toàn bộ Pipeline đã hoàn thành chu trình tự động!")
    except subprocess.CalledProcessError as e:
        print(f" [ERROR] Có lỗi xảy ra khi thực thi run_pipeline.py: {e}")
    except Exception as e:
        print(f" [ERROR] Lỗi hệ thống: {e}")

# ==========================================
# CẤU HÌNH THỜI GIAN CHẠY TỰ ĐỘNG
# ==========================================

# 1. Đặt lịch chạy định kỳ 00:00 hằng ngày
schedule.every().day.at("00:00").do(trigger_pipeline)

print("=" * 60)
print(" [AURA SCHEDULER SERVICE] Đã kích hoạt bộ canh giờ tự động ngầm!")
print(" Trạng thái: Đang ngồi canh lịch (00:00 hằng ngày)...")
print("  Lưu ý: Giữ Terminal này luôn bật để bộ lập lịch hoạt động.")
print("=" * 60)

# ==========================================
# TEST MODE: CHẠY LUÔN 1 LẦN NGAY KHI STARTUP
# ==========================================
print("\n[TEST MODE] Chạy thử nghiệm 1 lần duy nhất ngay khi vừa khởi động...")
trigger_pipeline()
print("[TEST MODE] Đã chạy xong lượt test đầu tiên! Chuyển sang chế độ chờ lịch 00:00...\n")

# Vòng lặp vô hạn chạy ngầm để ngồi canh đến 00:00
while True:
    schedule.run_pending()
    time.sleep(10)  # Check lịch mỗi 10s