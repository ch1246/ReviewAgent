"""LangGraph AgentState 定义。"""

from typing import Annotated, TypedDict
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """Agent 全局状态，所有节点共享。"""

    # 对话消息（自动追加，不覆盖）
    messages: Annotated[list, add_messages]

    # 当前执行步数（防止死循环）
    step_count: int

    # 最大步数限制
    max_steps: int

    # 是否已完成任务
    is_complete: bool

    # 错误信息（非空表示出错）
    error_message: str

    # 最终回答
    final_answer: str

    # session_id（用于 Redis 存取）
    session_id: str
