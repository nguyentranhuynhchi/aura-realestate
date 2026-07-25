import os
import subprocess
import sys
import json
import datetime
import csv
import shutil

# Định nghĩa các đường dẫn tuyệt đối
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
NEW_DATA_CSV = os.path.join(DATA_DIR, "new_data.csv")
LOG_FILE = os.path.join(BASE_DIR, "pipeline_log.json")

# Đường dẫn phục vụ MLOps Logistics
INTEGRATED_CLEAN_CSV = os.path.join(BASE_DIR, "data", "processed", "clean_data.csv")
SCALER_SOURCE = os.path.join(BASE_DIR, "backend", "models", "scaler.pkl") 
REGISTRY_DIR = os.path.join(BASE_DIR, "model_registry")

# Các script con
CRAWLER_SCRIPT = os.path.join(BASE_DIR, "crawler", "scripts", "run_crawler.py")
STAGE_1_PREPROCESS = os.path.join(BASE_DIR, "pipelines", "1_data_preprocessing.py")
STAGE_2_SPLIT = os.path.join(BASE_DIR, "pipelines", "2_split_train.py")
STAGE_3_TRAIN = os.path.join(BASE_DIR, "pipelines", "3_train.py")
STAGE_4_RAG = os.path.join(BASE_DIR, "pipelines", "4_text_chunking_rag.py")

def load_logs():
    if not os.path.exists(LOG_FILE):
        return {"last_crawl": "1970-01-01", "last_train": "1970-01-01"}
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"last_crawl": "1970-01-01", "last_train": "1970-01-01"}

def update_log(key, value_str):
    logs = load_logs()
    logs[key] = value_str
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=4, ensure_ascii=False)

def run_script(script_path, args=[]):
    print(f"\n[EXECUTE] Đang chạy: {os.path.basename(script_path)}...")
    result = subprocess.run([sys.executable, script_path] + args, capture_output=False, text=True)
    return result.returncode == 0

def clear_new_data():
    if os.path.exists(NEW_DATA_CSV):
        header = [
            "id", "title", "price_raw", "area_raw", "address_raw", "url", "seller_name", 
            "phone_number", "bedrooms", "bathrooms", "floors", "house_direction", 
            "legal_status", "interior", "ownership_type", "price_trend", "description", "surrounding_area"
        ]
        with open(NEW_DATA_CSV, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
        print(f"[CLEANUP] Đã làm trống vùng đệm {os.path.basename(NEW_DATA_CSV)} thành công.")

def main():
    today = datetime.date.today()
    logs = load_logs()
    
    last_crawl = datetime.datetime.strptime(logs["last_crawl"], "%Y-%m-%d").date()
    last_train = datetime.datetime.strptime(logs["last_train"], "%Y-%m-%d").date()
    
    print(f"=== KHỞI ĐỘNG HỆ THỐNG MLOPS PIPELINE [{today}] ===")
    
    # --- LUỒNG HÀNG NGÀY: CÀO DATA & LÀM SẠCH ---
    if today > last_crawl:
        print(f"\n[STATUS] Phát hiện ngày mới chưa cào (Lần cuối: {last_crawl}).")
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # 1. Cố gắng cào data (lỗi hay bị chặn cũng không sao, không để làm ngắt pipeline)
        run_script(CRAWLER_SCRIPT, args=["1", "3"])
        
        # 2. Luôn luôn chạy tiền xử lý dữ liệu nếu file new_data.csv có dữ liệu
        if run_script(STAGE_1_PREPROCESS):
            print("\n[RAG FLOW] Kích hoạt tiến trình chunking và đồng bộ Vector Database...")
            run_script(STAGE_4_RAG, args=["init_all"])
            clear_new_data()
            update_log("last_crawl", str(today))
            print(f"[SUCCESS] Hoàn thành xong luồng cào và xử lý hôm nay.")

    # --- LUỒNG ĐỊNH KỲ: RETRAIN MÔ HÌNH ML ---
    if (today - last_train).days >= 7:
        print(f"\n[STATUS] Đến lịch hẹn huấn luyện lại mô hình định kỳ (Chu kỳ 7 ngày).")
        
        # LOGIC DATA LOGISTICS: Đóng dấu thời gian ngay từ đầu luồng định kỳ
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        current_experiment_dir = os.path.join(REGISTRY_DIR, timestamp)
        os.makedirs(current_experiment_dir, exist_ok=True)
        print(f"\n[MLOPS LOGISTICS] Khởi tạo folder lịch sử cho chu kỳ retrain này: {timestamp}/")

        # Copy sẵn file data train sạch tổng hợp vào folder lịch sử trước
        if os.path.exists(INTEGRATED_CLEAN_CSV):
            shutil.copy(INTEGRATED_CLEAN_CSV, os.path.join(current_experiment_dir, "data_train.csv"))
            print(f"-> Đã lưu trữ thành công data_train.csv vào folder lịch sử.")

        # Kích hoạt file 2_split_train.py và TRUYỀN THÊM tham số timestamp sang
        split_success = run_script(STAGE_2_SPLIT, args=[timestamp])
        
        if split_success:
            # Kích hoạt file 3_train.py và truyền tên folder hiện tại qua để nó xử lý đối sánh mô hình
            train_success = run_script(STAGE_3_TRAIN, args=[timestamp])
            
            if train_success:
                update_log("last_train", str(today))
                print(f"[SUCCESS] Quy trình Full Retrain định kỳ hoàn thành xuất sắc!")

    else:
        days_left = 7 - (today - last_train).days
        print(f"\n[STATUS] Chưa đến lịch Retrain mô hình ML (Còn {days_left} ngày nữa).")

    print("\n=== HẾT CHU TRÌNH ĐIỀU PHỐI PIPELINE ===")

if __name__ == "__main__":
    main()