"""
==============================================================================
HUMAN GATE AGENT (MVP ARCHITECTURE - PURE PYTHON)
==============================================================================
Vai trò: Cổng kiểm duyệt chuyên gia con người & Thẩm định MLOps.
Nhiệm vụ:
1. Đóng phiên đo lường MTTR (Mean Time to Repair) và tính toán Pass@1, Pass@3.
2. Xuất bản Báo cáo Thẩm định Markdown (`agent/metrics/latest_audit_report.md`).
3. Biên soạn tệp PDF chuyên nghiệp đính kèm gửi Email cho quản trị viên.
4. Quyết định kết thúc chu trình Multi-Agent hoặc gửi cảnh báo can thiệp.
"""

import sys
import os
import tempfile
from typing import Dict, Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agent.core.state import AgentState
from agent.metrics.collector import metrics_collector
from agent.metrics.report import generate_enterprise_metrics_markdown
from agent.tools.pdf_report_generator import generate_audit_pdf_report
from agent.tools.alert_tools import send_email_alert


def human_gate_node(state: AgentState) -> Dict[str, Any]:
    """Node xử lý của Human Gate Agent."""
    print("\n [HUMAN GATE] Đang tổng hợp chỉ số doanh nghiệp & biên soạn báo cáo thẩm định...")

    dag_status = state.get("dag_status", "unknown")
    metrics = state.get("model_metrics", {})
    r2_score = metrics.get("r2")
    approved = state.get("human_approved", False)
    iterations = state.get("iteration_count", 0)

    # 1. KẾT THÚC PHIÊN ĐO LƯỜNG MTTR TRONG METRICS COLLECTOR
    final_status = "success" if (dag_status == "success" and approved) else "failed"
    last_msg = state.get("messages", [{}])[-1].get("content", "")
    session_data = metrics_collector.end_session(
        final_status=final_status,
        final_r2=r2_score,
        diagnosis=last_msg
    )

    duration = session_data.get("duration_seconds", 0.0)
    print(f" [HUMAN GATE METRICS]: MTTR={duration}s, Pass@{session_data.get('pass_at_k', 'N/A')}, R2={r2_score}")

    # 2. XUẤT BẢN BÁO CÁO THẨM ĐỊNH MARKDOWN
    md_content = generate_enterprise_metrics_markdown()
    report_path = os.path.join(os.path.dirname(__file__), "..", "metrics", "latest_audit_report.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f" [HUMAN GATE]: Đã xuất bản báo cáo Markdown tại: {os.path.abspath(report_path)}")

    # 3. BIÊN SOẠN FILE BÁO CÁO PDF
    pdf_path = os.path.join(tempfile.gettempdir(), "mlops_audit_report.pdf")
    try:
        generate_audit_pdf_report(state, output_path=pdf_path)
        print(f" [HUMAN GATE] Đã biên soạn xong file PDF: {pdf_path}")
    except Exception as e:
        print(f" [HUMAN GATE CẢNH BÁO]: Không thể tạo file PDF ({e}), tiếp tục tiến trình...")
        pdf_path = None

    # 4. GỬI EMAIL THÔNG BÁO CHO QUẢN TRỊ VIÊN
    status_label = "SUCCESS" if approved else "ACTION_REQUIRED"
    subject = f"Aura MLOps - Báo cáo vận hành: {status_label}"
    try:
        send_email_alert.invoke({
            "subject": subject,
            "diagnosis": last_msg,
            "diff_code": state.get("diff", ""),
            "status": status_label,
            "pdf_path": pdf_path
        })
        print(" [HUMAN GATE] Đã gửi báo cáo tổng hợp thành công về Email người quản trị!")
    except Exception as e:
        print(f" [HUMAN GATE]: Bỏ qua gửi email ({e})")

    return {
        "human_approved": approved,
        "next_step": "__end__"
    }
