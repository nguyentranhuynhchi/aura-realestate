"""
==============================================================================
AIRFLOW RUNNER AGENT (MVP ARCHITECTURE - PURE PYTHON)
==============================================================================
Vai trò: Kỹ sư vận hành hạ tầng & điều phối luồng MLOps.
Nhiệm vụ:
1. Giao tiếp với Airflow Webserver qua REST API để kích hoạt DAG.
2. Theo dõi trạng thái tiến trình chạy của DAG (Polling status).
3. Trích xuất nhật ký lỗi nếu tác vụ thất bại.
4. Cơ chế tự phục hồi (Local Fallback): Nếu Airflow tắt hoặc lỗi mạng, tự động
   nạp báo cáo kết quả MLOps gần nhất từ đĩa cứng mà không làm sập Agent.
"""

import sys
import os
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

    # 1. THỬ KÍCH HOẠT DAG TRÊN AIRFLOW WEBSERVER
    dag_id = os.getenv("AIRFLOW_DAG_ID", "aura_realestate_mlops_pipeline")
    trigger_res = trigger_airflow_dag(dag_id=dag_id)

    if trigger_res.get("success"):
        dag_run_id = trigger_res.get("dag_run_id")
        active_dag_id = trigger_res.get("dag_id", dag_id)
        print(f" [AIRFLOW RUNNER] Kích hoạt thành công Airflow DAG Run: {dag_run_id} (DAG: {active_dag_id})")
        
        # Kiểm tra trạng thái DAG
        status_res = get_dag_run_status(dag_id=active_dag_id, dag_run_id=dag_run_id)
        current_state = status_res.get("state", "running")
        
        if current_state == "failed":
            logs_res = get_failed_task_logs(dag_id=active_dag_id, dag_run_id=dag_run_id)
            return {
                "dag_run_id": dag_run_id,
                "dag_status": "failed",
                "failed_task_id": logs_res.get("failed_task_id"),
                "error_logs": logs_res.get("logs", "Không có log chi tiết."),
                "next_step": "supervisor"
            }
        else:
            return {
                "dag_run_id": dag_run_id,
                "dag_status": current_state,
                "next_step": "supervisor"
            }

    # 2. CƠ CHẾ TỰ PHỤC HỒI (LOCAL DISK FALLBACK NẾU AIRFLOW OFFLINE)
    print(f" [AIRFLOW RUNNER] Không kết nối được Airflow Webserver: {trigger_res.get('error')}")
    print(" [AIRFLOW RUNNER FALLBACK]: Đang nạp dữ liệu Pipeline Summary từ đĩa cứng...")

    summary_res = get_pipeline_summary()
    if summary_res.get("success"):
        data = summary_res.get("data", {})
        metrics = summary_res.get("metrics") or data.get("test_metrics", {})
        print(" [AIRFLOW RUNNER FALLBACK]: Đã nạp thành công dữ liệu Pipeline Summary gần nhất từ đĩa cứng.")
        return {
            "dag_run_id": "fallback_local_run",
            "dag_status": "success",
            "is_fallback": True,
            "fallback_reason": trigger_res.get("error", "Không thể kết nối Airflow Webserver"),
            "model_metrics": metrics,
            "error_logs": "",
            "next_step": "supervisor"
        }
    else:
        err_msg = f"Lỗi cả Airflow và Fallback đĩa: {summary_res.get('error')}"
        print(f" [AIRFLOW RUNNER LỖI]: {err_msg}")
        return {
            "dag_run_id": "failed_run",
            "dag_status": "failed",
            "error_logs": err_msg,
            "next_step": "supervisor"
        }
