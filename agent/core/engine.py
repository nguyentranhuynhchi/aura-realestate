"""
==============================================================================
AURA MLOPS WORKFLOW ENGINE (MVP ARCHITECTURE - DUAL ENGINE)
==============================================================================
Điều phối luồng thực thi Multi-Agent:
- Chế độ 1 (Production): Sử dụng LangGraph StateGraph nếu có cài đặt.
- Chế độ 2 (Native Fallback): Sử dụng Native Python State Machine (Zero-dependency),
  chạy ngay lập tức trên mọi môi trường mà không sợ lỗi thiếu package.
"""

import sys
from typing import Dict, Any, Callable

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agent.core.state import AgentState
from agent.agents.supervisor import supervisor_node
from agent.agents.coder import coder_node
from agent.agents.validator import validator_node
from agent.agents.airflow_runner import airflow_runner_node
from agent.agents.human_gate import human_gate_node


def run_native_workflow(initial_state: AgentState, max_steps: int = 15) -> AgentState:
    """
    Động cơ luồng thuần Python (Native State Machine Engine).
    Tự động điều phối trạng thái giữa các Node Agent mà không cần phụ thuộc bên ngoài.
    """
    current_state = dict(initial_state)
    current_node = "airflow_runner"
    step_count = 0

    nodes: Dict[str, Callable[[AgentState], Dict[str, Any]]] = {
        "airflow_runner": airflow_runner_node,
        "supervisor": supervisor_node,
        "coder": coder_node,
        "validator": validator_node,
        "human_gate": human_gate_node,
    }

    while current_node != "__end__" and step_count < max_steps:
        step_count += 1
        node_fn = nodes.get(current_node)
        if not node_fn:
            print(f" [ENGINE LỖI]: Không tìm thấy Node '{current_node}'!")
            break

        print(f"\n>>> [WORKFLOW ENGINE] Bước {step_count}: Đang thực thi Node '{current_node}'")
        updates = node_fn(current_state)
        current_state.update(updates)

        # Điều hướng trạng thái tiếp theo
        next_step = updates.get("next_step")
        if not next_step:
            if current_node == "airflow_runner":
                next_step = "supervisor"
            elif current_node == "coder":
                next_step = "validator"
            elif current_node == "validator":
                next_step = "airflow_runner" if updates.get("validation_status") == "passed" else "coder"
            elif current_node == "human_gate":
                next_step = "__end__"
            else:
                next_step = "__end__"

        current_node = next_step

    return current_state


def create_aura_workflow_graph():
    """
    Tạo đồ thị trạng thái LangGraph nếu môi trường có sẵn thư viện langgraph.
    Nếu chưa cài đặt, trả về hàm bao đóng chạy Native Engine.
    """
    try:
        from langgraph.graph import StateGraph, END

        workflow = StateGraph(AgentState)
        workflow.add_node("airflow_runner", airflow_runner_node)
        workflow.add_node("supervisor", supervisor_node)
        workflow.add_node("coder", coder_node)
        workflow.add_node("validator", validator_node)
        workflow.add_node("human_gate", human_gate_node)

        workflow.set_entry_point("airflow_runner")
        workflow.add_edge("airflow_runner", "supervisor")

        def supervisor_router(state: AgentState):
            return state.get("next_step", "human_gate")

        workflow.add_conditional_edges(
            "supervisor",
            supervisor_router,
            {
                "coder": "coder",
                "human_gate": "human_gate"
            }
        )

        workflow.add_edge("coder", "validator")

        def validator_router(state: AgentState):
            return "airflow_runner" if state.get("validation_status") == "passed" else "coder"

        workflow.add_conditional_edges(
            "validator",
            validator_router,
            {
                "airflow_runner": "airflow_runner",
                "coder": "coder"
            }
        )

        workflow.add_edge("human_gate", END)
        return workflow.compile()

    except ImportError:
        class NativeAppWrapper:
            def invoke(self, state: AgentState) -> AgentState:
                return run_native_workflow(state)

        return NativeAppWrapper()
