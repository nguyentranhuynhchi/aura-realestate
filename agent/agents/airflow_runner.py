"""
==============================================================================
AIRFLOW RUNNER AGENT (MVP ARCHITECTURE - PURE PYTHON)
==============================================================================
Vai trò: Kỹ sư vận hành hạ tầng & điều phối luồng MLOps.
Nhiệm vụ:
1. Giao tiếp với Airflow Webserver qua REST API để kích hoạt DAG.
2. Vòng lặp Polling (Đứng canh): Theo dõi liên tục cho đến khi DAG hoàn thành.
3. Trích xuất nhật ký lỗi nếu tác vụ thất bại (failed).
4. Cơ chế tự phục hồi (Local Fallback): Nếu Airflow tắt hoặc lỗi mạng, tự động
   nạp báo cáo kết quả MLOps gần nhất từ đĩa cứng mà không làm sập Agent.
==============================================================================
"""

import sys
import os
import time
from typing import Dict, Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agent.core.state import AgentState
from agent.tools.airflow_bridge import (
    trigger_airflow_dag,
    get_dag_run_status,
    get_failed_task_logs,
    get_pipeline_summary
)


def airflow_runner_node(state: AgentState) -> Dict[str, Any]:
    """Node xử lý của Airflow Runner Agent."""
    print("\n [AIRFLOW RUNNER] Đang chuẩn bị kích hoạt pipeline MLOps...")

    # 1. KÍCH HOẠT DAG TRÊN AIRFLOW WEBSERVER
    dag_id = os.getenv("AIRFLOW_DAG_ID", "aura_realestate_mlops_pipeline")
    trigger_res = trigger_airflow_dag(dag_id=dag_id)

    if trigger_res.get("success"):
        dag_run_id = trigger_res.get("dag_run_id")
        active_dag_id = trigger_res.get("dag_id", dag_id)
        print(f" [AIRFLOW RUNNER] Kích hoạt thành công Airflow DAG Run: {dag_run_id} (DAG: {active_dag_id})")
        
        # ----------------------------------------------------------------------
        # 2. VÒNG LẶP POLLING: ĐỨNG CANH CHỜ CHO ĐẾN KHI DAG CHẠY XONG
        # ----------------------------------------------------------------------
        max_wait_seconds = 300  # Chờ tối đa 5 phút
        poll_interval = 5       # Cứ 5 giây hỏi Airflow một lần
        elapsed = 0
        current_state = "queued"

        print(f" [AIRFLOW RUNNER] Đang theo dõi tiến trình thực thi DAG trên Airflow...")
        while elapsed < max_wait_seconds:
            status_res = get_dag_run_status(dag_id=active_dag_id, dag_run_id=dag_run_id)
            current_state = status_res.get("state", "unknown")

            # Nếu DAG đã chạy xong (thành công hoặc thất bại) thì thoát vòng lặp
            if current_state not in ("queued", "running"):
                print(f" [AIRFLOW RUNNER] DAG đã kết thúc với trạng thái: '{current_state.upper()}' (sau {elapsed}s).")
                break

            print(f" [AIRFLOW RUNNER] DAG đang xử lý (Trạng thái: '{current_state}', đã đợi {elapsed}s)...")
            time.sleep(poll_interval)
            elapsed += poll_interval

        # ----------------------------------------------------------------------
        # 3. PHÂN LOẠI KẾT QUẢ THỰC TẾ
        # ----------------------------------------------------------------------
        if current_state == "failed":
            logs_res = get_failed_task_logs(dag_id=active_dag_id, dag_run_id=dag_run_id)
            failed_task = logs_res.get("failed_task_id", "unknown_task")
            error_logs = logs_res.get("logs", "Không có log chi tiết.")
            print(f" [AIRFLOW RUNNER CẢNH BÁO]: Task '{failed_task}' bị lỗi thất bại!")
            return {
                "dag_run_id": dag_run_id,
                "dag_status": "failed",
                "failed_task_id": failed_task,
                "error_logs": error_logs,
                "is_fallback": False,
                "next_step": "supervisor"
            }
        elif current_state == "success":
            summary_res = get_pipeline_summary()
            summary_data = summary_res.get("data", {}) if summary_res.get("success") else {}
            metrics = summary_res.get("metrics", {}) if summary_res.get("success") else {}
            print(f" [AIRFLOW RUNNER]: Pipeline chạy thành công xuất sắc!")
            return {
                "dag_run_id": dag_run_id,
                "dag_status": "success",
                "model_metrics": metrics,
                "pipeline_summary": summary_data,
                "is_fallback": False,
                "next_step": "supervisor"
            }
        else:
            # Trường hợp quá thời gian chờ (Timeout)
            print(f" [AIRFLOW RUNNER]: DAG chưa kịp kết thúc sau {max_wait_seconds}s!")
            return {
                "dag_run_id": dag_run_id,
                "dag_status": "failed",
                "failed_task_id": "dag_timeout",
                "error_logs": f"DAG vượt quá thời gian chờ cho phép ({max_wait_seconds}s).",
                "is_fallback": False,
                "next_step": "supervisor"
            }

    # ----------------------------------------------------------------------
    # 4. CƠ CHẾ PHÒNG VỆ (LOCAL DISK FALLBACK NẾU MẤT KẾT NỐI WEBSERVER)
    # ----------------------------------------------------------------------
    error_msg = trigger_res.get('error', 'Airflow Timeout / Không phản hồi')
    print(f" [AIRFLOW RUNNER] Không kết nối được Airflow Webserver: {error_msg}")
    print(" [AIRFLOW RUNNER FALLBACK]: Đang nạp dữ liệu Pipeline Summary từ đĩa cứng...")

    summary_res = get_pipeline_summary()
    if summary_res.get("success"):
        data = summary_res.get("data", {})
        metrics = summary_res.get("metrics") or data.get("test_metrics", {})
        print(" [AIRFLOW RUNNER FALLBACK]: Đã nạp thành công dữ liệu Pipeline Summary gần nhất từ đĩa cứng.")
        return {
            "dag_run_id": "fallback_local_run",
            "dag_status": "degraded",
            "is_fallback": True,
            "fallback_reason": error_msg,
            "model_metrics": metrics,
            "pipeline_summary": data,
            "error_logs": error_msg,
            "next_step": "supervisor"
        }
    else:
        err_msg = f"Lỗi cả Airflow và Fallback đĩa: {summary_res.get('error')}"
        print(f" [AIRFLOW RUNNER LỖI]: {err_msg}")
        return {
            "dag_run_id": "failed_run",
            "dag_status": "failed",
            "error_logs": err_msg,
            "is_fallback": True,
            "next_step": "supervisor"
        }