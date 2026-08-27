import os
import json
import csv
import shutil
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.models import Variable
from airflow.utils.email import send_email

# ==========================================
# CẤU HÌNH CẢNH BÁO SỰ CỐ
# ==========================================
def send_failure_alert(context):
    task_instance = context.get('task_instance')
    task_id = task_instance.task_id
    dag_id = task_instance.dag_id
    exec_date = context.get('execution_date')
    log_url = task_instance.log_url
    exception = context.get('exception')

    # Lấy email nhận cảnh báo động từ Variable
    mlops_cfg = Variable.get("mlops_config", deserialize_json=True, default_var={})
    target_email = mlops_cfg.get("alert_email", "nguyentranhuynhchi@gmail.com")

    subject = f"🚨 [Aura MLOps] Task thất bại: {dag_id}.{task_id}"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px;">
        <h2 style="color: #d9534f;">⚠️ Pipeline MLOps phát hiện sự cố!</h2>
        <p><b>DAG ID:</b> {dag_id}</p>
        <p><b>Task bị lỗi:</b> <span style="color: red; font-weight: bold;">{task_id}</span></p>
        <p><b>Thời gian chạy:</b> {exec_date}</p>
        <p><b>Chi tiết ngoại lệ:</b> <pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; color: #c7254e;">{exception}</pre></p>
        <p><a href="{log_url}" style="background: #0275d8; color: white; padding: 8px 12px; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 10px;">Xem Log chi tiết trên UI</a></p>
    </div>
    """
    send_email(
        to=[target_email],
        subject=subject,
        html_content=html_content
    )

default_args = {
    'owner': 'aura_mlops',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(seconds=30),
    'on_failure_callback': send_failure_alert,
}

BASE_DIR = "/app"
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
NEW_DATA_CSV = os.path.join(DATA_DIR, "new_data.csv")
LOG_FILE = os.path.join(BASE_DIR, "pipeline_log.json")
INTEGRATED_CLEAN_CSV = os.path.join(BASE_DIR, "data", "processed", "clean_data.csv")
REGISTRY_DIR = os.path.join(BASE_DIR, "model_registry")

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

def post_crawl_cleanup():
    if os.path.exists(NEW_DATA_CSV):
        header = [
            "id", "title", "price_raw", "area_raw", "address_raw", "url", "seller_name", 
            "phone_number", "bedrooms", "bathrooms", "floors", "house_direction", 
            "legal_status", "interior", "ownership_type", "price_trend", "description", "surrounding_area"
        ]
        with open(NEW_DATA_CSV, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
        print(f"[CLEANUP] Đã làm trống vùng đệm {os.path.basename(NEW_DATA_CSV)}.")
    update_log("last_crawl", str(datetime.now().date()))

def check_weekly_retrain_branch():
    today = datetime.now().date()
    logs = load_logs()
    last_train = datetime.strptime(logs.get("last_train", "1970-01-01"), "%Y-%m-%d").date()
    
    # Đọc chu kỳ retrain động từ UI
    mlops_cfg = Variable.get("mlops_config", deserialize_json=True, default_var={"retrain_days_threshold": 7})
    threshold_days = mlops_cfg.get("retrain_days_threshold", 7)

    if (today - last_train).days >= threshold_days:
        return "init_mlops_logistics_task"
    return "skip_retrain_task"

def setup_mlops_logistics(**context):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_experiment_dir = os.path.join(REGISTRY_DIR, timestamp)
    os.makedirs(current_experiment_dir, exist_ok=True)
    print(f"[MLOPS LOGISTICS] Khởi tạo folder lịch sử: {timestamp}/")

    if os.path.exists(INTEGRATED_CLEAN_CSV):
        shutil.copy(INTEGRATED_CLEAN_CSV, os.path.join(current_experiment_dir, "data_train.csv"))
        print("-> Đã lưu trữ data_train.csv thành công.")

    context['task_instance'].xcom_push(key="retrain_timestamp", value=timestamp)

def mark_train_success():
    update_log("last_train", str(datetime.now().date()))
    print("[SUCCESS] Đã cập nhật mốc last_train mới.")

# ==========================================
# KHỞI TẠO ĐỒ THỊ DAG
# ==========================================
with DAG(
    "aura_realestate_mlops_pipeline",
    default_args=default_args,
    description="Pipeline cào dữ liệu, nạp ChromaDB và Retrain Stacking Model (Dynamic Variables)",
    schedule_interval=None,
    catchup=False,
) as dag:

    # Cào dữ liệu với số trang đọc động qua cú pháp Jinja template của Airflow
    crawl_task = BashOperator(
        task_id="crawl_raw_data",
        bash_command=(
            'python /app/crawler/scripts/run_crawler.py '
            '{{ var.json.mlops_config.crawl_start_page }} '
            '{{ var.json.mlops_config.crawl_end_page }}'
        ),
    )

    preprocess_task = BashOperator(
        task_id="preprocess_clean_data",
        bash_command="python /app/pipelines/1_data_preprocessing.py",
    )

    rag_sync_task = BashOperator(
        task_id="sync_chromadb_rag",
        bash_command="python /app/pipelines/4_text_chunking_rag.py init_all",
    )

    cleanup_task = PythonOperator(
        task_id="cleanup_and_update_crawl_log",
        python_callable=post_crawl_cleanup,
    )

    branch_task = BranchPythonOperator(
        task_id="check_weekly_retrain",
        python_callable=check_weekly_retrain_branch,
    )

    logistics_task = PythonOperator(
        task_id="init_mlops_logistics_task",
        python_callable=setup_mlops_logistics,
        provide_context=True,
    )

    split_task = BashOperator(
        task_id="split_data_task",
        bash_command='python /app/pipelines/2_split_train.py {{ ti.xcom_pull(task_ids="init_mlops_logistics_task", key="retrain_timestamp") }}',
    )

    train_task = BashOperator(
        task_id="train_stacking_model",
        bash_command='python /app/pipelines/3_train.py {{ ti.xcom_pull(task_ids="init_mlops_logistics_task", key="retrain_timestamp") }}',
    )

    update_train_log_task = PythonOperator(
        task_id="update_train_log_task",
        python_callable=mark_train_success,
    )

    skip_task = BashOperator(
        task_id="skip_retrain_task",
        bash_command='echo "[INFO] Chưa tới chu kỳ retrain model, bỏ qua huấn luyện."',
    )

    # Điều hướng luồng
    crawl_task >> preprocess_task >> rag_sync_task >> cleanup_task >> branch_task
    branch_task >> logistics_task >> split_task >> train_task >> update_train_log_task
    branch_task >> skip_task