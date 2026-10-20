# agent/monitoring/tracer.py
import os
import time
import logging
from typing import Any, Dict, List, Optional
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

# Cấu hình format log chuẩn cho Docker container
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [MLOPS-TRACER] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("MLOpsTracer")


def configure_langsmith():
    """
    Kích hoạt LangSmith Tracing nếu có API Key trong file .env.
    Giúp xem toàn bộ sơ đồ suy luận và dấu vết gọi tool trên giao diện web LangSmith.
    """
    api_key = os.getenv("LANGCHAIN_API_KEY")
    if api_key and api_key != "your_langsmith_api_key_here":
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "aura-agentic-mlops")
        logger.info(f" LangSmith Tracing đã BẬT | Project: {os.environ['LANGCHAIN_PROJECT']}")
    else:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        logger.info(" Chạy chế độ Local Logging Tracer (Không có LangSmith API Key).")


class MLOpsLoggingTracer(BaseCallbackHandler):
    """
    Custom Callback Handler theo dõi:
    - Thời gian phản hồi của từng Agent Node (Latency Tracking)
    - Số lượng Token tiêu thụ (Token Usage Tracking)
    - Trạng thái gọi Tool và lỗi phát sinh
    """
    def __init__(self):
        super().__init__()
        self.node_start_times: Dict[str, float] = {}

    def on_chain_start(
        self, serialized: Optional[Dict[str, Any]], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        chain_name = (serialized.get("name") if serialized else None) or "AgentNode"
        self.node_start_times[chain_name] = time.time()
        logger.info(f" BẮT ĐẦU NODE: [{chain_name}]")

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        logger.info(" HOÀN TẤT NODE.")

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        model = serialized.get("name", "vLLM-Local")
        total_chars = sum(len(p) for p in prompts)
        logger.info(f" [LLM Call] Gửi prompt tới mô hình {model} (Độ dài: {total_chars} ký tự)")

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        llm_output = response.llm_output or {}
        token_usage = llm_output.get("token_usage", {})
        if token_usage:
            prompt_tokens = token_usage.get("prompt_tokens", 0)
            completion_tokens = token_usage.get("completion_tokens", 0)
            total_tokens = token_usage.get("total_tokens", 0)
            logger.info(f" [Token Usage] Prompt={prompt_tokens} | Completion={completion_tokens} | Tổng={total_tokens}")
        else:
            logger.info(" [LLM Response] Đã nhận phản hồi từ LLM.")

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        tool_name = serialized.get("name", "Tool")
        logger.info(f" [TOOL BẮT ĐẦU] {tool_name} | Tham số: {input_str[:120]}...")

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        logger.info(f" [TOOL XONG] Kết quả: {output[:120]}...")

    def on_tool_error(self, error: BaseException, **kwargs: Any) -> None:
        logger.error(f" [TOOL GẶP LỖI]: {error}")


def get_tracer_callbacks() -> List[BaseCallbackHandler]:
    """
    Trả về danh sách Callbacks để nạp vào StateGraph config.
    """
    configure_langsmith()
    return [MLOpsLoggingTracer()]