"""
==============================================================================
AURA MLOPS MULTI-AGENT STATE DEFINITION (MVP ARCHITECTURE)
==============================================================================
Định nghĩa cấu trúc dữ liệu Bảng đen (Blackboard State) được truyền qua lại
giữa các nút Agent (Supervisor, Coder, Validator, Airflow Runner, Human Gate).
"""

import sys
from typing import TypedDict, Optional, List, Dict, Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class AgentState(TypedDict, total=False):
    """Trạng thái trung tâm (Blackboard State) của chu trình Multi-Agent MLOps MVP."""
    
    # 1. Trạng thái Pipeline & Airflow
    dag_run_id: str
    dag_status: str               # "success" | "failed" | "running" | "upstream_failed"
    error_logs: str               # Log lỗi trích xuất từ tác vụ thất bại
    failed_task_id: Optional[str] # Tên task bị hỏng (ví dụ: 'tune_ridge_task')
    
    # 2. Ngữ cảnh sửa lỗi & Mã nguồn
    target_file: Optional[str]    # Đường dẫn tệp mục tiêu (ví dụ: 'pipelines/6_modeling/01_tune_ridge.py')
    original_code: Optional[str]  # Nội dung code gốc trước khi sửa
    proposed_code: Optional[str]  # Nội dung code mới do Coder Agent đề xuất
    diff: Optional[str]           # Bản so sánh Git Unified Diff (đỏ/xanh) giữa code cũ và mới
    
    # 3. Thẩm định & Kiểm thử an toàn Sandbox
    validation_status: str        # "pending" | "passed" | "failed"
    validation_error: Optional[str] # Chi tiết lỗi khi nạp module hoặc chạy smoke test
    
    # 4. Chỉ số mô hình ML (Stacking Regressor)
    model_metrics: Dict[str, Any] # {'r2': 0.72, 'mae': 0.26, 'rmse': 0.37}
    
    # 5. Kiểm soát vòng lặp tự chữa lành (Self-Healing Loop)
    iteration_count: int          # Số lần Agent đã cố gắng sửa code (tối đa max_iterations)
    max_iterations: int           # Ngưỡng dừng tối đa (mặc định = 3 để tính Pass@3)
    human_approved: bool          # Đã được người quản trị hoặc cổng Human Gate duyệt
    
    # 6. Nhật ký đối thoại & Đo lường doanh nghiệp
    messages: List[Dict[str, Any]]
    session_id: str               # Mã định danh phiên sửa lỗi (dùng tính MTTR)
    start_time: float             # Thời điểm bắt đầu phát hiện sự cố
