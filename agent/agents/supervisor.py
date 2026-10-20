"""
==============================================================================
SUPERVISOR AGENT (MVP ARCHITECTURE - PURE PYTHON)
==============================================================================
Vai trò: Trưởng nhóm giám sát (Orchestrator).
Nhiệm vụ:
1. Đọc kết quả Pipeline MLOps & độ đo mô hình (R2, MAE, RMSE).
2. Chẩn đoán nguyên nhân khi pipeline gặp sự cố.
3. Đối chiếu danh mục 24 micro-modules để tìm tệp mã nguồn mục tiêu (target_file).
4. Điều phối luồng làm việc tới Coder, Validator hoặc Human Gate.
"""

import sys
import os
import re
from typing import Dict, Any, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agent.core.state import AgentState
from agent.tools.sandbox import list_catalog_modules
from agent.metrics.collector import metrics_collector


def resolve_target_file(failed_task_id: Optional[str], error_logs: str) -> Optional[str]:
    """
    Phân giải chính xác file mã nguồn liên quan dựa trên danh mục 24 micro-modules.
    Không dùng regex mò mẫm hay phụ thuộc vào cấu trúc text ngẫu nhiên của LLM.
    """
    catalog = list_catalog_modules()
    combined_text = f"{failed_task_id or ''} {error_logs or ''}".lower()

    # Bảng ánh xạ từ khóa task sang file cụ thể
    task_mapping = {
        "tune_ridge": "pipelines/6_modeling/01_tune_ridge.py",
        "tune_lightgbm": "pipelines/6_modeling/02_tune_lightgbm.py",
        "tune_xgboost": "pipelines/6_modeling/03_tune_xgboost.py",
        "tune_catboost": "pipelines/6_modeling/04_tune_catboost.py",
        "stacking": "pipelines/6_modeling/05_stacking_meta_learner.py",
        "evaluate": "pipelines/6_modeling/06_evaluate_and_log.py",
        "shap": "pipelines/6_modeling/07_shap_explainer.py",
        "register": "pipelines/6_modeling/08_register_model.py",
        "segment": "pipelines/3_preprocessing/01_segment_filter.py",
        "outlier": "pipelines/3_preprocessing/02_outlier_removal.py",
        "impute": "pipelines/3_preprocessing/03_imputation_and_scaling.py",
        "target": "pipelines/3_preprocessing/04_target_transform.py",
        "split": "pipelines/4_split/01_spatial_temporal_split.py",
        "feature": "pipelines/2_feature_eng/01_advanced_features.py",
        "clean": "pipelines/1_eda/01_clean_and_eda.py",
        "crawler": "crawler/batdongsan_crawler.py",
        "predict": "backend/app/api/endpoints/predict.py",
        "rag": "backend/app/api/endpoints/rag.py"
    }

    # 1. So khớp theo từ khóa task
    for kw, path in task_mapping.items():
        if kw in combined_text:
            return path

    # 2. So khớp trực tiếp tên file có trong catalog
    for module_path in catalog:
        module_name = os.path.basename(module_path).lower()
        if module_name in combined_text:
            return module_path

    return None


def supervisor_node(state: AgentState) -> Dict[str, Any]:
    """Node xử lý của Supervisor Agent."""
    print("\n [SUPERVISOR] Đang đọc trạng thái trên bảng đen để chẩn đoán...")
    
    dag_status = state.get("dag_status", "unknown")
    metrics = state.get("model_metrics", {})
    r2_score = metrics.get("r2", 0.0)
    iterations = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", 3)
    error_logs = state.get("error_logs", "")
    failed_task_id = state.get("failed_task_id")

    # 1. KHỞI ĐỘNG PHIÊN ĐO LƯỜNG MTTR NẾU CHƯA CÓ
    if not metrics_collector.current_session:
        session_id = state.get("session_id", f"session_{iterations}")
        reason = f"DAG_{dag_status}" if dag_status != "success" else "MODEL_EVALUATION"
        metrics_collector.start_session(session_id, trigger_reason=reason, initial_r2=r2_score)

    # 2. TRƯỜNG HỢP 1: PIPELINE THÀNH CÔNG VÀ CHỈ SỐ MÔ HÌNH ĐẠT CHUẨN AN TOÀN
    if dag_status == "success" and r2_score >= 0.65:
        fallback_notice = ""
        if state.get("is_fallback"):
            fallback_notice = (
                f"[CẢNH BÁO VẬN HÀNH]: Tuần này Airflow gặp sự cố kết nối!\n"
                f"-> Chi tiết lỗi: {state.get('fallback_reason', 'Lỗi mạng / Webserver offline')}\n"
                f"-> Hệ thống tạm thời nạp kết quả đã lưu từ phiên trước trên đĩa cứng để báo cáo.\n\n"
            )

        diagnosis = (
            f"{fallback_notice}"
            f"Pipeline MLOps hoàn thành xuất sắc!\n"
            f"- Đánh giá mô hình: ĐẠT CHUẨN AN TOÀN VẬN HÀNH với R2 = {r2_score} "
            f"(Ngưỡng yêu cầu >= 0.65), MAE = {metrics.get('mae', 'N/A')}, RMSE = {metrics.get('rmse', 'N/A')}.\n"
            f"- Trạng thái: Sẵn sàng phân phối mô hình mới ra Production Backend."
        )
        print(f"\n[SUPERVISOR TỔNG KẾT]:\n{diagnosis}")
        return {
            "messages": [{"role": "supervisor", "content": diagnosis}],
            "human_approved": True,
            "next_step": "human_gate"
        }

    # 3. TRƯỜNG HỢP 2: ĐÃ VƯỢT QUÁ SỐ VÒNG LẶP SỬA LỖI (QUÁ TẢI PASS@K)
    if iterations >= max_iter:
        diagnosis = (
            f"[CẢNH BÁO QUÁ VÒNG LẶP]: Đã thử sửa lỗi {iterations}/{max_iter} lần nhưng chưa đạt chuẩn.\n"
            f"Dừng vòng lặp tự động để chuyển sang chuyên gia con người can thiệp (Human-in-the-Loop)."
        )
        print(f"\n[SUPERVISOR]: {diagnosis}")
        return {
            "messages": [{"role": "supervisor", "content": diagnosis}],
            "human_approved": False,
            "next_step": "human_gate"
        }

    # 4. TRƯỜNG HỢP 3: PIPELINE THẤT BẠI HOẶC R2 DƯỚI NGƯỠNG (CẦN SỬA LỖI / TINH CHỈNH)
    target_file = resolve_target_file(failed_task_id, error_logs)
    if not target_file:
        # Nếu R2 thấp mà không có lỗi cụ thể, mặc định tối ưu meta learner hoặc ridge
        target_file = "pipelines/6_modeling/01_tune_ridge.py"

    diagnosis = (
        f"Phát hiện sự cố cần khắc phục (Vòng {iterations + 1}/{max_iter}):\n"
        f"- Trạng thái DAG: {dag_status} (Task: {failed_task_id or 'Quality Gate'})\n"
        f"- Chỉ số hiện tại: R2 = {r2_score} (Yêu cầu >= 0.65)\n"
        f"- Tệp mục tiêu can thiệp: '{target_file}'\n"
        f"- Nhiệm vụ: Giao quyền cho Coder Agent phân tích và đề xuất bản vá an toàn."
    )
    print(f"\n[SUPERVISOR ĐIỀU PHỐI]:\n{diagnosis}")

    return {
        "target_file": target_file,
        "messages": [{"role": "supervisor", "content": diagnosis}],
        "next_step": "coder"
    }
