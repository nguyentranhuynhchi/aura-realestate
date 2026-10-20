"""
==============================================================================
TEST SUITE: AURA MLOPS PYTHON TOOLS (MVP ARCHITECTURE)
==============================================================================
Kiểm thử chuyên sâu các công cụ nền tảng:
1. Rào chắn cú pháp AST (validate_python_syntax)
2. Thao tác tệp an toàn (read/write sandbox file)
3. Sinh bản so sánh Git Unified Diff
4. Kiểm tra nạp module cô lập trong Subprocess
5. Đọc tóm tắt pipeline (Local Fallback)
6. Đo lường chỉ số doanh nghiệp (MTTR, Pass@k)
"""

import os
import sys
from pathlib import Path

# Đảm bảo import được module agent từ thư mục gốc
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agent.tools.sandbox import (
    read_sandbox_file,
    write_sandbox_file,
    validate_python_syntax,
    generate_code_diff,
    list_catalog_modules
)
from agent.tools.test_runner import check_module_importability
from agent.tools.airflow_bridge import get_pipeline_summary
from agent.metrics.collector import metrics_collector


def test_ast_syntax_checker():
    print("\n[TEST 1] Kiểm thử rào chắn cú pháp AST (ast.parse)...")
    
    # Đoạn mã chuẩn
    valid_code = "def add(a, b):\n    return a + b\n"
    is_valid, msg, line, col = validate_python_syntax(valid_code)
    assert is_valid is True, "Mã hợp lệ phải trả về True"
    print(f" -> PASS: {msg}")

    # Đoạn mã cố tình sai cú pháp (thiếu đóng ngoặc)
    invalid_code = "def broken_func(:\n    pass\n"
    is_valid, msg, line, col = validate_python_syntax(invalid_code)
    assert is_valid is False, "Mã sai cú pháp phải trả về False"
    assert line > 0, "Phải xác định được dòng lỗi"
    print(f" -> PASS Bắt lỗi cú pháp chính xác: Dòng {line}, Cột {col}")


def test_safe_file_write_with_ast_guard():
    print("\n[TEST 2] Kiểm thử Ghi file có rào chắn AST (write_sandbox_file)...")
    
    # Cố tình ghi mã lỗi cú pháp
    bad_code = "class BadSyntax\n    def __init__(self): pass"
    res = write_sandbox_file("test_broken.py", bad_code)
    assert res["success"] is False, "Hệ thống bắt buộc phải từ chối ghi mã lỗi cú pháp"
    print(f" -> PASS: Rào chắn AST đã chặn đứng ghi mã hỏng thành công.")

    # Ghi mã chuẩn
    good_code = "# Unit test safe write\nx = 100\n"
    res = write_sandbox_file("test_clean.py", good_code)
    assert res["success"] is True, "Mã hợp lệ phải được ghi thành công"
    print(f" -> PASS: {res['message']}")


def test_read_file_and_diff():
    print("\n[TEST 3] Kiểm thử đọc file và sinh Git Diff...")
    
    catalog = list_catalog_modules()
    assert len(catalog) == 24, "Danh mục phải đủ 24 micro-modules"
    
    # Đọc thử 1 file trong catalog
    target = "pipelines/6_modeling/01_tune_ridge.py"
    res = read_sandbox_file(target)
    assert res["success"] is True, f"Phải đọc được file {target}"
    print(f" -> PASS: Đọc thành công '{target}' ({res['line_count']} dòng)")

    # Sinh Git Diff
    diff = generate_code_diff(res["content"], res["content"] + "\n# Extra line\n", filename=target)
    assert "+# Extra line" in diff, "Bản diff phải hiển thị dòng mới thêm vào"
    print(" -> PASS: Sinh Git Unified Diff chính xác.")


def test_isolated_subprocess_import():
    print("\n[TEST 4] Kiểm thử nạp module trong Subprocess cô lập...")
    target = "pipelines/6_modeling/01_tune_ridge.py"
    res = check_module_importability(target)
    assert res["success"] is True, f"Nạp {target} phải thành công"
    print(f" -> PASS: {res['message']}")


def test_pipeline_summary_fallback():
    print("\n[TEST 5] Kiểm thử đọc tóm tắt MLOps (Local Fallback)...")
    res = get_pipeline_summary()
    assert res["success"] is True, "Phải đọc được file pipeline_summary.json trên đĩa"
    metrics = res.get("metrics") or res["data"].get("test_metrics", {})
    assert "r2" in metrics, "Dữ liệu tóm tắt phải chứa chỉ số R2"
    print(f" -> PASS: Đã đọc chỉ số từ đĩa: R2 = {metrics['r2']}, MAE = {metrics.get('mae')}")


def test_enterprise_metrics_collector():
    print("\n[TEST 6] Kiểm thử đo lường chỉ số doanh nghiệp (MTTR & Pass@k)...")
    session = metrics_collector.start_session("unit_test_session_001", trigger_reason="TEST_EVAL", initial_r2=0.50)
    assert session["session_id"] == "unit_test_session_001"

    metrics_collector.log_tool_call("validate_python_syntax", success=True)
    metrics_collector.log_iteration(iteration=1, target_file="01_tune_ridge.py", syntax_valid=True, test_passed=True)
    
    res = metrics_collector.end_session(final_status="success", final_r2=0.72)
    assert res["status"] == "success"
    assert res["duration_seconds"] >= 0.0
    print(f" -> PASS: Phiên đo lường kết thúc thành công: MTTR = {res['duration_seconds']}s, Pass@{res['pass_at_k']}")


if __name__ == "__main__":
    print("==================================================")
    print(" BẮT ĐẦU KIỂM THỬ BỘ CÔNG CỤ MULTI-AGENT MVP")
    print("==================================================")
    test_ast_syntax_checker()
    test_safe_file_write_with_ast_guard()
    test_read_file_and_diff()
    test_isolated_subprocess_import()
    test_pipeline_summary_fallback()
    test_enterprise_metrics_collector()
    print("==================================================")
    print(" TOÀN BỘ 6 BÀI KIỂM THỬ CÔNG CỤ ĐÃ VƯỢT QUA 100%!")
    print("==================================================")
