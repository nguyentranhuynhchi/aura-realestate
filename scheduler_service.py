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
        # Sử dụng sys.executable để đảm bảo gọi đúng môi trường Python hiện tại của máy thật
        result = subprocess.run([sys.executable, "run_pipeline.py"], check=True)
        print(f" [{datetime.now().strftime('%H:%M:%S')}] Toàn bộ Pipeline đã hoàn thành chu trình tự động!")
    except subprocess.CalledProcessError as e:
        print(f" [ERROR] Có lỗi xảy ra khi thực thi run_pipeline.py: {e}")
    except Exception as e:
        print(f" [ERROR] Lỗi hệ thống: {e}")

# ==========================================
# CẤU HÌNH THỜI GIAN CHẠY TỰ ĐỘNG 
# ==========================================

# 1. Cấu hình thực tế (Chạy cào dữ liệu hằng ngày vào lúc 00:00 đêm)
# schedule.every().day.at("00:00").do(trigger_pipeline)
schedule.every(10).seconds.do(trigger_pipeline)

# 2. Cấu hình kiểm thử 
# schedule.every(5).minutes.do(trigger_pipeline)

print("=" * 60)
print(" [AURA SCHEDULER SERVICE] Đã kích hoạt bộ canh giờ tự động ngầm!")
print(f" Trạng thái: Đang ngồi canh lịch (00:00 hằng ngày)...")
print("  Lưu ý: Giữ Terminal này luôn bật để bộ lập lịch hoạt động.")
print("=" * 60)

# Vòng lặp vô hạn chạy ngầm để liên tục kiểm tra đồng hồ máy tính
while True:
    schedule.run_pending()
    time.sleep(5)  # Cứ 30 giây kiểm tra lịch hẹn một lần (không hề tốn CPU)