"""
==============================================================================
AURA MLOPS MULTI-AGENT MAIN RUNNER (MVP ARCHITECTURE)
==============================================================================
Điểm khởi động chính của Hệ thống Multi-Agent MLOps Tự hành:
- Chế độ 1: '--mode once' -> Chạy một phiên thẩm định / vá lỗi MLOps duy nhất.
- Chế độ 2: '--mode daemon' -> Tiến trình giám sát ngầm theo chu kỳ.
"""

import os
import sys
import time
import signal
import argparse
import logging
from datetime import datetime
from typing import Dict, Any

# Đảm bảo đường dẫn gốc của project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Đảm bảo UTF-8 an toàn trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agent.core.state import AgentState
from agent.core.engine import create_aura_workflow_graph, run_native_workflow
from agent.metrics.collector import metrics_collector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [AURA-AGENT-MAIN] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("AuraAgentMain")

IS_RUNNING = True


def handle_exit_signal(signum, frame):
    global IS_RUNNING
    logger.info("Nhận tín hiệu dừng tiến trình. Đang thoát an toàn...")
    IS_RUNNING = False


signal.signal(signal.SIGINT, handle_exit_signal)
signal.signal(signal.SIGTERM, handle_exit_signal)


def run_agent_workflow(session_id: str = "mlops_run_default") -> Dict[str, Any]:
    """Khởi chạy một phiên Multi-Agent hoàn chỉnh từ đầu đến cuối."""
    logger.info("==================================================")
    logger.info(f" KHỞI CHẠY PHIÊN MULTI-AGENT MLOPS MVP | ID: {session_id}")
    logger.info("==================================================")

    initial_state: AgentState = {
        "dag_run_id": session_id,
        "dag_status": "pending",
        "error_logs": "",
        "failed_task_id": None,
        "target_file": None,
        "original_code": None,
        "proposed_code": None,
        "diff": None,
        "validation_status": "pending",
        "validation_error": None,
        "model_metrics": {},
        "iteration_count": 0,
        "max_iterations": 3,
        "human_approved": False,
        "messages": [],
        "session_id": session_id,
        "start_time": time.time()
    }

    try:
        app = create_aura_workflow_graph()
        if hasattr(app, "invoke"):
            final_state = app.invoke(initial_state)
        else:
            final_state = run_native_workflow(initial_state)

        last_msg = ""
        if final_state.get("messages"):
            last_msg = final_state["messages"][-1].get("content", "")

        logger.info("==================================================")
        logger.info(" PHIÊN MULTI-AGENT MLOPS ĐÃ HOÀN THÀNH!")
        logger.info(f" Trạng thái DAG cuối cùng: {final_state.get('dag_status')}")
        logger.info(f" Số vòng lặp sửa code: {final_state.get('iteration_count')}")
        logger.info(f" Kết quả: {last_msg}")
        logger.info("==================================================")
        return final_state
    except Exception as e:
        logger.error(f" Lỗi trong quá trình chạy Multi-Agent: {e}", exc_info=True)
        return {}


def main():
    parser = argparse.ArgumentParser(description="Aura Real Estate Multi-Agent MLOps Runner")
    parser.add_argument(
        "--mode",
        choices=["once", "daemon"],
        default="once",
        help="Chế độ chạy: 'once' (chạy 1 lần) hoặc 'daemon' (chạy tiến trình nền giám sát liên tục)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Khoảng thời gian nghỉ giữa các chu kỳ giám sát trong chế độ daemon (giây, mặc định 300s)"
    )
    args = parser.parse_args()

    if args.mode == "once":
        session_id = f"mlops_manual_{int(time.time())}"
        run_agent_workflow(session_id=session_id)
    elif args.mode == "daemon":
        logger.info(f"Khởi động Multi-Agent Daemon Worker (Chu kỳ kiểm tra: {args.interval}s)...")
        while IS_RUNNING:
            session_id = f"mlops_daemon_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                run_agent_workflow(session_id=session_id)
            except Exception as e:
                logger.error(f"Lỗi phiên daemon: {e}")

            logger.info(f"Nghỉ {args.interval} giây trước chu kỳ giám sát kế tiếp...")
            for _ in range(args.interval):
                if not IS_RUNNING:
                    break
                time.sleep(1)

        logger.info("Multi-Agent Daemon Worker đã dừng an toàn.")


if __name__ == "__main__":
    main()
