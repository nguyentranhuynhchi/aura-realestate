"""
==============================================================================
VALIDATOR AGENT (MVP ARCHITECTURE - PURE PYTHON)
==============================================================================
Vai trò: Kỹ sư kiểm thử & đảm bảo chất lượng (QA / Test Engineer).
Nhiệm vụ:
1. Thẩm định mã nguồn trong môi trường Sandbox cô lập trước khi cho phép chạy thật.
2. Kiểm tra nạp module động trong một tiến trình con riêng (Isolated Subprocess).
3. Chạy các bài kiểm thử khói (Smoke Tests) để xác nhận dữ liệu và logic không bị gãy.
4. Quyết định bật "Đèn xanh" (Passed) cho Airflow Runner hay trả về Coder sửa tiếp.
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
from agent.tools.test_runner import check_module_importability, run_preprocessing_smoke_test
from agent.metrics.collector import metrics_collector


def validator_node(state: AgentState) -> Dict[str, Any]:
    """Node xử lý của Validator Agent."""
    target_file = state.get("target_file", "")
    iteration = state.get("iteration_count", 1)
    val_status = state.get("validation_status", "pending")
    val_error = state.get("validation_error")

    print(f"\n [VALIDATOR] Đang thẩm định tính toàn vẹn của Sandbox sau khi vá '{target_file}'...")

    # 1. NẾU CODER ĐÃ BÁO LỖI TỪ TRƯỚC (VÍ DỤ SAI CÚ PHÁP AST)
    if val_status == "failed" and val_error:
        print(f" [VALIDATOR]: Từ chối thẩm định do lỗi có sẵn từ Coder: {val_error}")
        return {
            "validation_status": "failed",
            "validation_error": val_error,
            "next_step": "coder"
        }

    # 2. KIỂM THỬ TẦNG 1: THỬ NẠP MODULE TRONG SUBPROCESS CÔ LẬP
    if target_file:
        print(f" [VALIDATOR TẦNG 1]: Thử nạp module '{target_file}' trong tiến trình độc lập...")
        import_res = check_module_importability(target_file)
        if not import_res.get("success"):
            err_msg = f"Lỗi nạp module (Import/Runtime Error):\n{import_res.get('error')}"
            print(f" [VALIDATOR PHÁT HIỆN LỖI]: {err_msg}")
            
            # Cập nhật kết quả test vào metrics
            metrics_collector.log_iteration(iteration, target_file, syntax_valid=True, test_passed=False)
            
            return {
                "validation_status": "failed",
                "validation_error": err_msg,
                "error_logs": err_msg,
                "next_step": "coder"
            }
        print(" [VALIDATOR TẦNG 1]: Nạp module thành công tuyệt đối!")

    # 3. KIỂM THỬ TẦNG 2: CHẠY SMOKE TEST NẾU LÀ TỆP TIỀN XỬ LÝ (PREPROCESSING)
    if "preprocessing" in target_file:
        print(" [VALIDATOR TẦNG 2]: Chạy Smoke Test luồng tiền xử lý dữ liệu...")
        smoke_res = run_preprocessing_smoke_test()
        if not smoke_res.get("success"):
            err_msg = f"Lỗi Smoke Test tiền xử lý:\n{smoke_res.get('error')}"
            print(f" [VALIDATOR PHÁT HIỆN LỖI]: {err_msg}")
            metrics_collector.log_iteration(iteration, target_file, syntax_valid=True, test_passed=False)
            return {
                "validation_status": "failed",
                "validation_error": err_msg,
                "error_logs": err_msg,
                "next_step": "coder"
            }
        print(" [VALIDATOR TẦNG 2]: Smoke Test tiền xử lý vượt qua 100%!")

    # 4. TẤT CẢ KIỂM THỬ ĐÃ ĐẠT: BẬT ĐÈN XANH CHO AIRFLOW RUNNER
    print(" [VALIDATOR]: Thẩm định toàn vẹn Sandbox THÀNH CÔNG! Bật đèn xanh cho Airflow Runner.")
    metrics_collector.log_iteration(iteration, target_file, syntax_valid=True, test_passed=True)

    return {
        "validation_status": "passed",
        "validation_error": None,
        "next_step": "airflow_runner"
    }
