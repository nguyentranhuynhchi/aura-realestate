import os
import csv
import json
import shutil
from datetime import datetime, timedelta

from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

# Cấu hình mặc định cho các Task trong DAG
default_args = {
    "owner": "aura_mlops",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(seconds=30),
}

# Định nghĩa các đường dẫn tài nguyên dùng chung trong container
BASE_DIR = "/app"
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
NEW_DATA_CSV = os.path.join(DATA_DIR, "new_data.csv")
LOG_FILE = os.path.join(BASE_DIR, "pipeline_log.json")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
INTEGRATED_CLEAN_CSV = os.path.join(PROCESSED_DIR, "clean_data.csv")
REGISTRY_DIR = os.path.join(BASE_DIR, "model_registry")


def load_logs() -> dict:
    """Đọc file nhật ký pipeline, tự khởi tạo mốc mặc định nếu file chưa tồn tại."""
    if not os.path.exists(LOG_FILE):
        return {"last_crawl": "1970-01-01", "last_train": "1970-01-01"}
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"last_crawl": "1970-01-01", "last_train": "1970-01-01"}


def update_log(key: str, value_str: str) -> None:
    """Cập nhật mốc thời gian thực thi của từng giai đoạn vào pipeline_log.json."""
    logs = load_logs()
    logs[key] = value_str
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=4, ensure_ascii=False)


def setup_mlops_logistics(**context) -> None:
    """Khởi tạo thư mục experiment mới theo timestamp và lưu snapshot dữ liệu."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_experiment_dir = os.path.join(REGISTRY_DIR, timestamp)
    os.makedirs(current_experiment_dir, exist_ok=True)

    if os.path.exists(INTEGRATED_CLEAN_CSV):
        shutil.copy(INTEGRATED_CLEAN_CSV, os.path.join(current_experiment_dir, "data_train.csv"))

    context["task_instance"].xcom_push(key="retrain_timestamp", value=timestamp)


def finalize_pipeline_summary(**context) -> dict:
    """Đọc file pipeline_summary.json do run_pipeline.py sinh ra và đẩy vào XCom cho Supervisor."""
    ti = context["task_instance"]
    timestamp = ti.xcom_pull(task_ids="init_mlops_logistics_task", key="retrain_timestamp")
    
    exp_dir = os.path.join(REGISTRY_DIR, timestamp) if timestamp else None
    summary_path = os.path.join(exp_dir, "pipeline_summary.json") if exp_dir else None

    summary_payload = {}
    if summary_path and os.path.exists(summary_path):
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                summary_payload = json.load(f)
        except Exception as e:
            summary_payload = {"status": "error", "message": f"Lỗi đọc file summary: {str(e)}"}
    else:
        summary_payload = {"status": "error", "message": f"Không tìm thấy file: {summary_path}"}

    summary_payload["dag_run_id"] = context.get("dag_run").run_id if context.get("dag_run") else timestamp
    summary_payload["completed_at"] = datetime.now().isoformat()

    update_log("last_train", str(datetime.now().date()))
    
    # Trả về giá trị này để Airflow tự động lưu vào XCom (return_value)
    return summary_payload


# Khởi tạo đồ thị DAG ở chế độ bị động: schedule_interval=None
with DAG(
    "aura_realestate_mlops_pipeline",
    default_args=default_args,
    description="Pipeline MLOps vi mô (Micro-modules) tự hành thu thập, làm sạch và tái huấn luyện Stacking Regressor",
    schedule_interval=None,
    catchup=False,
) as dag:

    # 1. Khởi tạo logistic & timestamp thí nghiệm
    logistics_task = PythonOperator(
        task_id="init_mlops_logistics_task",
        python_callable=setup_mlops_logistics,
        provide_context=True,
    )

    # 2. Thu thập dữ liệu qua Crawler micro-modules
    crawl_task = BashOperator(
        task_id="crawl_raw_data",
        bash_command=(
            "python /app/crawler/scripts/run_crawler.py "
            "{{ var.json.mlops_config.crawl_start_page }} "
            "{{ var.json.mlops_config.crawl_end_page }}"
        ),
    )

    # 3. Chạy luồng Micro-Modules MLOps Pipeline (Hỗ trợ linh hoạt baseline hoặc update_code qua dag_run.conf)
    run_modular_pipeline_task = BashOperator(
        task_id="run_modular_mlops_pipeline",
        bash_command=(
            'python {{ dag_run.conf.get("pipeline_dir", "/app/agent/sandbox/baseline") }}/run_pipeline.py '
            '{{ ti.xcom_pull(task_ids="init_mlops_logistics_task", key="retrain_timestamp") }}'
        ),
    )

    # 4. Đóng gói và đẩy trọn vẹn Metadata của 22 file con vào XCom cho Supervisor Agent
    finalize_summary_task = PythonOperator(
        task_id="finalize_pipeline_summary",
        python_callable=finalize_pipeline_summary,
        provide_context=True,
    )

    # Chuỗi thực thi thẳng
    logistics_task >> crawl_task >> run_modular_pipeline_task >> finalize_summary_task