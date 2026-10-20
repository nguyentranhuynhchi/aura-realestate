# agent/memory/state.py
"""
Bảng đen trạng thái chung (Shared State) của hệ thống Aura Multi-Agent.
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated

try:
    from langchain_core.messages import AnyMessage
    from langgraph.graph.message import add_messages
except ImportError:
    # Fallback cho môi trường kiểm thử nhẹ không có langchain/langgraph
    AnyMessage = Any
    def add_messages(existing: List[Any], new: List[Any]) -> List[Any]:
        return (existing or []) + (new or [])


class AgentState(TypedDict):
    """
    Tấm bảng đen (Shared State) lưu trữ toàn bộ trạng thái của hệ thống MLOps Agent.
    """
    # 1. Hộp thư hội thoại (lưu lịch sử trao đổi và kết quả gọi Tool của LangGraph)
    messages: Annotated[List[AnyMessage], add_messages]

    # 2. Thông tin lượt chạy Airflow
    dag_run_id: Optional[str]           # ID của lượt chạy Airflow hiện tại
    dag_status: str                     # 'running', 'success', hoặc 'failed'
    pipeline_dir: str                   # '/app/pipelines' (gốc) hoặc '/app/agent/sandbox/update_code' (thử nghiệm)

    # 3. Chẩn đoán sự cố & Báo cáo số liệu
    error_context: Optional[Dict[str, Any]]   # Chứa task bị lỗi và Traceback log
    model_metrics: Optional[Dict[str, Any]]   # Điểm R2, MAE, RMSE của Challenger vs Champion
    pipeline_summary: Optional[Dict[str, Any]] # Toàn bộ metadata tổng hợp nhận từ XCom
    diagnosis: Optional[str]                  # 'Căn bệnh' do Supervisor phân tích bằng lời

    # 4. Quản lý bản vá mã nguồn (Code Patch)
    target_file: Optional[str]          # Tên file cần sửa (ví dụ: '6_modeling/01_tune_ridge.py')
    code_patch: Optional[str]           # Nội dung mã nguồn mới do Coder Agent viết trong sandbox
    code_diff: Optional[str]            # Bản so sánh Git Diff (+ thêm, - bớt) gửi cho bạn duyệt

    # 5. Cầu dao an toàn & Quyết định của Con người
    iteration_count: int                # Số vòng lặp tự sửa lỗi đã chạy (1, 2, 3)
    human_approved: Optional[bool]      # None (đang chờ), True (Bạn bấm Duyệt), False (Từ chối)
    next_step: Optional[str]            # Bước tiếp theo cần rẽ nhánh trong đồ thị
