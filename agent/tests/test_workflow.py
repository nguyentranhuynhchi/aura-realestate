"""
==============================================================================
TEST SUITE: AURA MLOPS MULTI-AGENT WORKFLOW (MVP ARCHITECTURE)
==============================================================================
Kiểm thử toàn diện luồng điều phối Multi-Agent MLOps:
1. Supervisor phân giải target_file an toàn (Catalog Resolution).
2. Supervisor chẩn đoán và định tuyến khi Model đạt chuẩn.
3. Coder và Validator thẩm định tính toàn vẹn Sandbox.
4. Human Gate xuất bản báo cáo chỉ số doanh nghiệp.
5. Kiểm thử luồng khép kín End-to-End từ đầu đến cuối.
"""

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agent.core.state import AgentState
from agent.core.engine import run_native_workflow
from agent.agents.supervisor import supervisor_node, resolve_target_file
from agent.agents.coder import coder_node
from agent.agents.validator import validator_node
from agent.agents.human_gate import human_gate_node


def test_supervisor_catalog_resolution():
    print("\n[TEST 1] Kiểm tra giải quyết file mục tiêu (Catalog Resolution)...")
    
    # Giả lập log lỗi từ Airflow task
    target = resolve_target_file("tune_ridge_task", "Traceback in 01_tune_ridge.py line 45")
    assert target == "pipelines/6_modeling/01_tune_ridge.py"
    print(f" -> PASS: Phân giải chính xác tác vụ tune_ridge -> {target}")

    target_prep = resolve_target_file("segment_filter_task", "Error filtering segments")
    assert target_prep == "pipelines/3_preprocessing/01_segment_filter.py"
    print(f" -> PASS: Phân giải chính xác tác vụ preprocessing -> {target_prep}")


def test_supervisor_routing_success():
    print("\n[TEST 2] Kiểm thử Supervisor khi Pipeline đạt chuẩn an toàn...")
    
    state: AgentState = {
        "dag_run_id": "test_run_success",
        "dag_status": "success",
        "model_metrics": {"r2": 0.74, "mae": 0.15, "rmse": 0.22},
        "iteration_count": 0,
        "max_iterations": 3,
        "messages": []
    }
    
    result = supervisor_node(state)
    assert result["next_step"] == "human_gate"
    assert result["human_approved"] is True
    print(" -> PASS: Supervisor nhận diện mô hình đạt chuẩn và định tuyến thẳng tới Human Gate.")


def test_coder_and_validator_safety_flow():
    print("\n[TEST 3] Kiểm thử Coder & Validator qua rào chắn Sandbox...")
    
    state: AgentState = {
        "dag_run_id": "test_patch_run",
        "target_file": "pipelines/6_modeling/01_tune_ridge.py",
        "error_logs": "Optimize hyperparameter alpha for higher R2",
        "iteration_count": 0,
        "max_iterations": 3
    }
    
    # 1. Coder sinh code và kiểm tra AST
    coder_out = coder_node(state)
    assert coder_out["validation_status"] in ("pending", "passed")
    assert coder_out["diff"] is not None
    print(f" -> PASS Coder: Đã sinh bản vá và vượt qua AST Guard.")

    # 2. Validator thẩm định trong Subprocess cô lập
    state.update(coder_out)
    val_out = validator_node(state)
    assert val_out["validation_status"] == "passed"
    assert val_out["next_step"] == "airflow_runner"
    print(" -> PASS Validator: Đã thẩm định thành công và bật đèn xanh cho Airflow Runner.")


def test_human_gate_and_metrics_report():
    print("\n[TEST 4] Kiểm thử Human Gate & Enterprise Metrics Report...")
    
    state: AgentState = {
        "dag_run_id": "test_eval_final",
        "dag_status": "success",
        "model_metrics": {"r2": 0.73, "mae": 0.25, "rmse": 0.35},
        "human_approved": True,
        "iteration_count": 1,
        "messages": [{"role": "supervisor", "content": "Mô hình đạt chuẩn sản xuất."}],
        "diff": "--- original\n+++ proposed\n+ alpha=0.5\n"
    }
    
    result = human_gate_node(state)
    assert result["next_step"] == "__end__"
    
    # Kiểm tra file báo cáo Markdown
    report_file = ROOT_DIR / "agent" / "metrics" / "latest_audit_report.md"
    assert report_file.exists(), "Tệp báo cáo Markdown phải được tạo thành công"
    content = report_file.read_text(encoding="utf-8")
    assert "BÁO CÁO THẨM ĐỊNH HIỆU NĂNG" in content
    print(f" -> PASS: Human Gate đã xuất bản thành công Báo cáo Chỉ số Doanh nghiệp ({len(content)} ký tự).")


def test_end_to_end_native_workflow():
    print("\n[TEST 5] Kiểm thử Native Workflow hoàn chỉnh từ đầu đến cuối...")
    
    initial_state: AgentState = {
        "dag_run_id": "test_e2e_run",
        "dag_status": "pending",
        "error_logs": "",
        "iteration_count": 0,
        "max_iterations": 3,
        "session_id": "e2e_session_test"
    }
    
    final_state = run_native_workflow(initial_state, max_steps=10)
    assert final_state.get("dag_status") in ("degraded", "success")
    assert final_state.get("is_fallback") is True or final_state.get("dag_status") == "success"
    print(f" -> PASS: Toàn bộ luồng Multi-Agent E2E đã chạy thành công, kết quả: {final_state.get('dag_status')}")


if __name__ == "__main__":
    print("==================================================")
    print(" BẮT ĐẦU KIỂM THỬ LUỒNG MULTI-AGENT MLOPS MVP")
    print("==================================================")
    test_supervisor_catalog_resolution()
    test_supervisor_routing_success()
    test_coder_and_validator_safety_flow()
    test_human_gate_and_metrics_report()
    test_end_to_end_native_workflow()
    print("==================================================")
    print(" TOÀN BỘ 5 BÀI KIỂM THỬ MULTI-AGENT MVP ĐÃ VƯỢT QUA 100%!")
    print("==================================================")
