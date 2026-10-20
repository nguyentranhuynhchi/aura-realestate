# agent/metrics/collector.py
"""
Bộ thu thập & quản trị độ đo thực chiến (Enterprise Metrics Engine)
Dành cho hệ thống Aura Multi-Agent MLOps Platform.
"""
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
METRICS_DIR = os.path.join(BASE_DIR, "metrics")
METRICS_FILE = os.path.join(METRICS_DIR, "agent_metrics_history.json")


class EnterpriseMetricsCollector:
    """Bộ thu thập chỉ số vận hành chuẩn doanh nghiệp (MTTR, Pass@k, Tool Reliability)."""

    def __init__(self, metrics_file: str = METRICS_FILE):
        self.metrics_file = metrics_file
        self.current_session: Optional[Dict[str, Any]] = None

    def start_session(self, session_id: str, trigger_reason: str, initial_r2: Optional[float] = None) -> Dict[str, Any]:
        """Khởi động đồng hồ bấm giờ tính MTTR cho một phiên xử lý sự cố."""
        self.current_session = {
            "session_id": session_id,
            "trigger_reason": trigger_reason,
            "start_time": time.time(),
            "start_timestamp": datetime.now().isoformat(),
            "initial_r2": initial_r2,
            "iterations": [],
            "tool_calls": 0,
            "failed_tool_calls": 0,
            "final_status": "in_progress"
        }
        return self.current_session

    def log_tool_call(self, tool_name: str, success: bool, latency_ms: float = 0.0):
        """Ghi nhận độ tin cậy của mỗi lần gọi Tool."""
        if self.current_session:
            self.current_session["tool_calls"] += 1
            if not success:
                self.current_session["failed_tool_calls"] += 1

    def log_iteration(self, iteration: int, target_file: str, syntax_valid: bool, test_passed: bool):
        """Ghi nhận kết quả từng vòng lặp sửa lỗi của Coder."""
        if self.current_session:
            self.current_session["iterations"].append({
                "iteration": iteration,
                "target_file": target_file,
                "syntax_valid": syntax_valid,
                "test_passed": test_passed,
                "timestamp": datetime.now().isoformat()
            })

    def end_session(self, final_status: str, final_r2: Optional[float] = None, diagnosis: str = "") -> Dict[str, Any]:
        """Kết thúc phiên, tính toán MTTR và lưu trữ vào lịch sử."""
        if not self.current_session:
            return {}

        end_time = time.time()
        start_time = self.current_session["start_time"]
        duration = round(end_time - start_time, 2)

        iteration_count = len(self.current_session["iterations"])
        pass_at_k = iteration_count if final_status == "success" else None

        record = {
            "session_id": self.current_session["session_id"],
            "trigger_reason": self.current_session["trigger_reason"],
            "start_timestamp": self.current_session["start_timestamp"],
            "end_timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "mttr_minutes": round(duration / 60.0, 2),
            "status": final_status,
            "iteration_count": max(1, iteration_count),
            "pass_at_k": pass_at_k,
            "initial_r2": self.current_session["initial_r2"],
            "final_r2": final_r2,
            "r2_improvement": round((final_r2 - (self.current_session["initial_r2"] or 0)), 4) if final_r2 and self.current_session["initial_r2"] else 0.0,
            "tool_calls": self.current_session["tool_calls"],
            "failed_tool_calls": self.current_session["failed_tool_calls"],
            "tool_reliability_pct": round(
                (1.0 - (self.current_session["failed_tool_calls"] / max(1, self.current_session["tool_calls"]))) * 100, 2
            ),
            "diagnosis": diagnosis,
            "iterations_detail": self.current_session["iterations"]
        }

        # Lưu vào đĩa
        history = self.get_all_history()
        history.append(record)
        os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
        with open(self.metrics_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

        self.current_session = None
        return record

    def get_all_history(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.metrics_file):
            return []
        try:
            with open(self.metrics_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def compute_summary_stats(self) -> Dict[str, Any]:
        """Tính toán tổng hợp các chỉ số KPI doanh nghiệp của hệ thống Multi-Agent."""
        history = self.get_all_history()
        if not history:
            return {
                "total_runs": 0,
                "mttr_avg_seconds": 0.0,
                "pass_at_1_rate": "0%",
                "pass_at_3_rate": "0%",
                "tool_reliability_rate": "100%",
                "overall_success_rate": "0%"
            }

        total = len(history)
        successes = [h for h in history if h.get("status") == "success"]

        # MTTR trung bình
        avg_mttr = sum(h["duration_seconds"] for h in successes) / max(1, len(successes))
        
        # Pass@1 và Pass@3
        p1 = len([h for h in successes if h.get("pass_at_k") == 1])
        p3 = len([h for h in successes if h.get("pass_at_k") in [1, 2, 3]])

        # Độ tin cậy công cụ
        avg_tool_rel = sum(h.get("tool_reliability_pct", 100.0) for h in history) / total

        return {
            "total_runs": total,
            "successful_runs": len(successes),
            "overall_success_rate": f"{(len(successes) / total) * 100:.1f}%",
            "mttr_avg_seconds": round(avg_mttr, 1),
            "mttr_avg_minutes": round(avg_mttr / 60.0, 2),
            "pass_at_1_rate": f"{(p1 / total) * 100:.1f}%",
            "pass_at_3_rate": f"{(p3 / total) * 100:.1f}%",
            "tool_reliability_rate": f"{avg_tool_rel:.1f}%",
            "latest_run": history[-1]
        }


# Singleton instance dùng chung
metrics_collector = EnterpriseMetricsCollector()
