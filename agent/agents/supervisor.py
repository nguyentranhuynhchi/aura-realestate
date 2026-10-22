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
    Phân giải chính xác file mã nguồn liên quan dựa trên danh mục 24 micro-modules thực tế của Aura.
    Ưu tiên tìm kiếm tên file khớp với catalog, sau đó dùng ánh xạ từ khóa chuẩn xác.
    """
    catalog = list_catalog_modules()
    combined_text = f"{failed_task_id or ''} {error_logs or ''}".lower()

    # 1. So khớp trực tiếp tên file hoặc một phần đường dẫn có trong catalog
    for module_path in catalog:
        module_name = os.path.basename(module_path).lower()
        stem_name = os.path.splitext(module_name)[0]
        clean_stem = stem_name.split("_", 1)[-1] if "_" in stem_name else stem_name
        
        if module_name in combined_text or stem_name in combined_text or clean_stem in combined_text or module_path.lower() in combined_text:
            return f"pipelines/{module_path}"

    # 2. Bảng ánh xạ từ khóa nghiệp vụ chuẩn theo đúng 24 micro-modules thực tế của dự án
    keyword_mapping = {
        # 1_crawler
        "session": "pipelines/1_crawler/01_session_cookie.py",
        "cookie": "pipelines/1_crawler/01_session_cookie.py",
        "spider": "pipelines/1_crawler/02_api_spider.py",
        "crawler": "pipelines/1_crawler/02_api_spider.py",
        "crawl": "pipelines/1_crawler/02_api_spider.py",
        "raw_extractor": "pipelines/1_crawler/03_raw_extractor.py",
        # 2_eda
        "missing_audit": "pipelines/2_eda/01_missing_audit.py",
        "collinearity": "pipelines/2_eda/02_collinearity_check.py",
        "skew": "pipelines/2_eda/03_distribution_skew.py",
        "outlier": "pipelines/2_eda/04_iqr_outlier_audit.py",
        "iqr": "pipelines/2_eda/04_iqr_outlier_audit.py",
        # 3_preprocessing
        "segment": "pipelines/3_preprocessing/01_segment_filter.py",
        "numeric": "pipelines/3_preprocessing/02_numeric_parser.py",
        "bounds": "pipelines/3_preprocessing/03_physical_bounds.py",
        "district": "pipelines/3_preprocessing/04_district_encoder.py",
        "category": "pipelines/3_preprocessing/05_category_encoder.py",
        "imputer": "pipelines/3_preprocessing/06_missing_imputer.py",
        "impute": "pipelines/3_preprocessing/06_missing_imputer.py",
        "deduplicator": "pipelines/3_preprocessing/07_deduplicator.py",
        "dedup": "pipelines/3_preprocessing/07_deduplicator.py",
        # 4_rag
        "chunk": "pipelines/4_rag/01_chunk_builder.py",
        "chroma": "pipelines/4_rag/02_chroma_syncer.py",
        "syncer": "pipelines/4_rag/02_chroma_syncer.py",
        # 5_split
        "splitter": "pipelines/5_split/01_data_splitter.py",
        "split": "pipelines/5_split/01_data_splitter.py",
        "log_transform": "pipelines/5_split/02_log_transform.py",
        "scaler": "pipelines/5_split/03_feature_scaler.py",
        "scale": "pipelines/5_split/03_feature_scaler.py",
        # 6_modeling
        "ridge": "pipelines/6_modeling/01_tune_ridge.py",
        "tune_ridge": "pipelines/6_modeling/01_tune_ridge.py",
        "tree": "pipelines/6_modeling/02_tune_tree.py",
        "tune_tree": "pipelines/6_modeling/02_tune_tree.py",
        "rf": "pipelines/6_modeling/03_tune_rf.py",
        "random_forest": "pipelines/6_modeling/03_tune_rf.py",
        "tune_rf": "pipelines/6_modeling/03_tune_rf.py",
        "stacking": "pipelines/6_modeling/04_train_stacking.py",
        "train_stacking": "pipelines/6_modeling/04_train_stacking.py",
        "evaluate": "pipelines/6_modeling/05_evaluate_champion.py",
        "champion": "pipelines/6_modeling/05_evaluate_champion.py"
    }

    for kw, path in keyword_mapping.items():
        if kw in combined_text:
            return path

    return None


def supervisor_node(state: AgentState) -> Dict[str, Any]:
    """Node xử lý của Supervisor Agent."""
    print("\n [SUPERVISOR] Đang đọc trạng thái trên bảng đen để chẩn đoán...")
    
    dag_status = state.get("dag_status", "unknown")
    metrics = state.get("model_metrics", {})
    r2_score = metrics.get("r2") if metrics.get("r2") is not None else metrics.get("R2_score", 0.0)
    iterations = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", 3)
    error_logs = state.get("error_logs", "")
    failed_task_id = state.get("failed_task_id")
    is_fallback = state.get("is_fallback", False)

    # 1. KHỞI ĐỘNG PHIÊN ĐO LƯỜNG MTTR NẾU CHƯA CÓ
    if not metrics_collector.current_session:
        session_id = state.get("session_id", f"session_{iterations}")
        reason = f"DAG_{dag_status}" if dag_status != "success" else "MODEL_EVALUATION"
        metrics_collector.start_session(session_id, trigger_reason=reason, initial_r2=r2_score)

    # 2. TRƯỜNG HỢP 1: PHÒNG VỆ KHI AIRFLOW GẶP SỰ CỐ / TIMEOUT (FALLBACK ĐĨA CỨNG)
    if is_fallback or dag_status == "degraded":
        fallback_err = state.get("fallback_reason") or "Airflow Webserver không phản hồi (Timeout / Offline)"
        diagnosis = (
            f"[CẢNH BÁO HẠ TẦNG MLOPS]: Airflow gặp sự cố kết nối!\n"
            f"-> Chi tiết lỗi: {fallback_err}\n"
            f"-> Cơ chế phòng vệ: Nạp snapshot dữ liệu đệm từ phiên trước để duy trì giám sát.\n"
            f"-> Trạng thái dữ liệu: Snapshot có R2 = {r2_score} (Dữ liệu tuần này CHƯA được cập nhật).\n"
            f"-> Khuyến nghị: Kiểm tra container aura_airflow_webserver hoặc mạng nội bộ Docker."
        )
        print(f"\n[SUPERVISOR CẢNH BÁO]:\n{diagnosis}")
        return {
            "messages": [{"role": "supervisor", "content": diagnosis}],
            "supervisor_diagnosis": diagnosis,
            "human_approved": False,
            "status_label": "DEGRADED",
            "next_step": "human_gate"
        }

    # 3. TRƯỜNG HỢP 2: PIPELINE THỰC TẾ THÀNH CÔNG VÀ CHỈ SỐ MÔ HÌNH ĐẠT CHUẨN AN TOÀN
    if dag_status == "success" and r2_score >= 0.65:
        prev_r2 = metrics.get("previous_champion_r2", "N/A")
        is_promoted = metrics.get("is_promoted", False) or metrics.get("status") in ["Champion", "Champion_Candidate"]
        staged_dir = metrics.get("staged_experiment_dir") or "model_registry/"
        
        deploy_info = (
            f"- Trạng thái Deploy: CHỜ DEVELOPER PHÊ DUYỆT (Chưa đưa lên Production).\n"
            f"- Mô hình ứng viên: R2 = {r2_score} (Vượt qua mốc cũ R2 = {prev_r2}).\n"
            f"- Vị trí lưu trữ: {staged_dir}\n"
            f"- Hành động: Để deploy mô hình này, Developer chạy: python -m agent.tools.deploy_model --latest"
            if is_promoted else
            f"- Trạng thái Deploy: GIỮ NGUYÊN MÔ HÌNH CŨ (Mô hình mới R2={r2_score} chưa vượt mốc Champion cũ {prev_r2})."
        )
        
        diagnosis = (
            f"Pipeline MLOps hoàn thành xuất sắc!\n"
            f"- Đánh giá mô hình: ĐẠT CHUẨN AN TOÀN VẬN HÀNH với R2 = {r2_score} "
            f"(Ngưỡng yêu cầu >= 0.65), MAE = {metrics.get('mae', metrics.get('MAE', 'N/A'))}, RMSE = {metrics.get('rmse', metrics.get('RMSE', 'N/A'))}.\n"
            f"{deploy_info}"
        )
        print(f"\n[SUPERVISOR TỔNG KẾT]:\n{diagnosis}")
        return {
            "messages": [{"role": "supervisor", "content": diagnosis}],
            "supervisor_diagnosis": diagnosis,
            "human_approved": True,
            "status_label": "SUCCESS",
            "next_step": "human_gate"
        }

    # 4. TRƯỜNG HỢP 3: ĐÃ VƯỢT QUÁ SỐ VÒNG LẶP SỬA LỖI (QUÁ TẢI PASS@K)
    if iterations >= max_iter:
        diagnosis = (
            f"[CẢNH BÁO QUÁ VÒNG LẶP]: Đã thử sửa lỗi {iterations}/{max_iter} lần nhưng chưa đạt chuẩn.\n"
            f"Dừng vòng lặp tự động để chuyển sang chuyên gia con người can thiệp (Human-in-the-Loop)."
        )
        print(f"\n[SUPERVISOR]: {diagnosis}")
        return {
            "messages": [{"role": "supervisor", "content": diagnosis}],
            "supervisor_diagnosis": diagnosis,
            "human_approved": False,
            "status_label": "ACTION_REQUIRED",
            "next_step": "human_gate"
        }

    # 5. TRƯỜNG HỢP 4: PIPELINE THẤT BẠI HOẶC R2 DƯỚI NGƯỠNG (CẦN SỬA LỖI / TINH CHỈNH)
    target_file = resolve_target_file(failed_task_id, error_logs)
    if not target_file:
        # Nếu R2 thấp mà không có lỗi cú pháp, tự động tìm micro-module có R2 thấp nhất trong pipeline_summary
        summary = state.get("pipeline_summary", {})
        steps_6 = summary.get("steps", {}).get("6_modeling", {})
        if steps_6:
            r_scores = {
                "pipelines/6_modeling/04_train_stacking.py": steps_6.get("stacking", {}).get("val_r2", 1.0),
                "pipelines/6_modeling/03_tune_rf.py": steps_6.get("rf", {}).get("val_r2", 1.0),
                "pipelines/6_modeling/02_tune_tree.py": steps_6.get("tree", {}).get("val_r2", 1.0),
                "pipelines/6_modeling/01_tune_ridge.py": steps_6.get("ridge", {}).get("val_r2", 1.0),
            }
            lowest_file = min(r_scores, key=lambda k: r_scores[k] if isinstance(r_scores[k], (int, float)) else 1.0)
            target_file = lowest_file
        else:
            target_file = "pipelines/6_modeling/04_train_stacking.py"

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
        "supervisor_diagnosis": diagnosis,
        "next_step": "coder"
    }
