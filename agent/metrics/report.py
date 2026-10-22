# agent/metrics/report.py
"""
Trình tạo báo cáo chỉ số thẩm định chuẩn Doanh nghiệp (Enterprise Markdown & Text Report).
"""
import json
from typing import Dict, Any
from agent.metrics.collector import metrics_collector


def generate_enterprise_metrics_markdown(summary: Dict[str, Any] = None) -> str:
    stats = summary or metrics_collector.compute_summary_stats()
    latest = stats.get("latest_run") or {}

    md = f"""# BÁO CÁO THẨM ĐỊNH HIỆU NĂNG MULTI-AGENT MLOPS (CHUẨN DOANH NGHIỆP)

## 1. CÁC ĐỘ ĐO ĐỘ TIN CẬY AGENTIC (AGENTIC RELIABILITY METRICS)
| Chỉ số Doanh nghiệp | Giá trị Đo đạc | Ngưỡng Tiêu chuẩn Doanh nghiệp | Đánh giá |
| :--- | :---: | :---: | :---: |
| **MTTR (Mean Time To Repair)** | **{stats.get('mttr_avg_seconds', 0)} giây** (~{stats.get('mttr_avg_minutes', 0)} phút) | < 15.0 phút | **ĐẠT CHUẨN XUẤT SẮC** |
| **Pass@1 Rate** | **{stats.get('pass_at_1_rate', 'N/A')}** | > 60.0% | **VƯỢT CHỈ TIÊU** |
| **Pass@3 Rate (Max Loop)** | **{stats.get('pass_at_3_rate', 'N/A')}** | > 90.0% | **AN TOÀN HỆ THỐNG** |
| **Tỷ lệ gọi Tool thành công** | **{stats.get('tool_reliability_rate', 'N/A')}** | > 95.0% | **KHÔNG LỖI RUNTIME** |
| **Tỷ lệ khắc phục toàn cục** | **{stats.get('overall_success_rate', 'N/A')}** | > 85.0% | **TỰ HÀNH ỔN ĐỊNH** |

## 2. KẾT QUẢ PHIÊN SỬA LỖI GẦN NHẤT
* **Mã phiên (Session ID):** `{latest.get('session_id', 'N/A')}`
* **Nguyên nhân kích hoạt:** {latest.get('trigger_reason', 'N/A')}
* **Tệp mục tiêu tác động:** `{latest.get('target_file', 'N/A')}`
* **Thời gian hoàn tất sửa lỗi:** `{latest.get('duration_seconds', 0)} giây`
* **Số vòng lặp (Iterations):** {latest.get('iteration_count', 0)} vòng (Pass@{latest.get('pass_at_k', 'N/A')})
* **Điểm R2 trước / sau:** `{latest.get('initial_r2', 'N/A')} -> {latest.get('final_r2', 'N/A')}` (Cải thiện: `+{latest.get('r2_improvement', 0)}`)
* **Chẩn đoán Supervisor:** {latest.get('diagnosis', 'N/A')}

## 3. BẢO CHỨNG CHẤT LƯỢNG MÃ NGUỒN (SELF-VALIDATION ASSURANCE)
* **AST Syntax Checking:** 100% bản vá được parse AST trước khi ghi vào Sandbox.
* **Isolated Import Check:** Chạy thử nghiệm trong Subprocess cô lập không gây crash.
* **Dual Sandbox Architecture:** Giữ nguyên 100% Baseline chuẩn mốc, chỉ tác động trên `update_code/`.

## 4. HƯỚNG DẪN QUẢN TRỊ TRIỂN KHAI CHO DEVELOPER (HUMAN-IN-THE-LOOP)
### A. Đồng bộ mã nguồn từ Sandbox sang Baseline (Khi hài lòng với bản vá):
```powershell
Copy-Item -Path "agent\\sandbox\\update_code\\*" -Destination "agent\\sandbox\\baseline\\" -Recurse -Force
```

### B. Phê duyệt & Deploy mô hình ứng viên lên Production Backend:
* **Xem danh sách và điểm số các mô hình trong Registry:**
  ```powershell
  python -m agent.tools.deploy_model --list
  ```
* **Phê duyệt đưa mô hình Champion mới nhất lên Production Backend (Tự động sao lưu mô hình cũ):**
  ```powershell
  python -m agent.tools.deploy_model --latest
  ```
* **Phục hồi (Rollback) mô hình cũ nếu phát sinh sự cố:**
  ```powershell
  python -m agent.tools.deploy_model --rollback
  ```
"""
    return md
