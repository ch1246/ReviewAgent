"""LangGraph 编排：定义 Agent 工作流。"""

from langgraph.graph import StateGraph, END
from core.state import AgentState
from core.llm import chat
from tools.base import get_tool_definitions, execute_tool
from config import settings


def agent_node(state: AgentState) -> dict:
    """Agent 节点：调用 LLM，决定回答还是调工具。"""
    messages = state["messages"]
    system = state.get("_system_prompt", "")
    tools = get_tool_definitions()

    try:
        response = chat(messages=list(messages), system=system, tools=tools)
    except Exception as e:
        return {
            "error_message": str(e),
            "is_complete": True,
            "final_answer": f"调用 LLM 出错：{e}",
            "step_count": state["step_count"] + 1,
        }

    result = {
        "step_count": state["step_count"] + 1,
    }

    # 有文本回复
    if response["text"]:
        result["final_answer"] = response["text"]

    # 有工具调用 → 把 LLM 回复加入消息，不标记完成
    if response["tool_calls"]:
        # 构造 assistant 消息
        assistant_content = []
        if response["text"]:
            assistant_content.append({"type": "text", "text": response["text"]})
        for tc in response["tool_calls"]:
            assistant_content.append({
                "type": "tool_use",
                "id": tc["id"],
                "name": tc["name"],
                "input": tc["args"],
            })
        result["messages"] = [{"role": "assistant", "content": assistant_content}]
        result["is_complete"] = False
    else:
        # 没有工具调用 → 任务完成
        if response["text"]:
            result["messages"] = [{"role": "assistant", "content": response["text"]}]
        result["is_complete"] = True

    return result


def tool_node(state: AgentState) -> dict:
    """工具执行节点：执行 LLM 请求的工具调用。"""
    messages = list(state["messages"])
    last_message = messages[-1]

    # 从最后一条 assistant 消息中提取 tool_use
    tool_calls = []
    if isinstance(last_message.get("content"), list):
        for block in last_message["content"]:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                tool_calls.append(block)

    if not tool_calls:
        return {"is_complete": True}

    # 执行每个工具
    new_messages = []
    for tc in tool_calls:
        result = execute_tool(tc["name"], tc["input"])
        new_messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tc["id"],
                "content": result,
            }],
        })

    return {"messages": new_messages}


def should_continue(state: AgentState) -> str:
    """条件边：判断是继续调工具还是结束。"""
    # 已完成
    if state.get("is_complete"):
        return "end"

    # 超过最大步数
    if state["step_count"] >= state["max_steps"]:
        return "end"

    # 有错误
    if state.get("error_message"):
        return "end"

    # 继续
    return "continue"


def build_graph():
    """构建 LangGraph 图。"""
    workflow = StateGraph(AgentState)

    # 注册节点
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)

    # 入口
    workflow.set_entry_point("agent")

    # 条件边：agent → 继续调工具 or 结束
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end": END,
        },
    )

    # tools → agent（执行完工具回到 agent）
    workflow.add_edge("tools", "agent")

    return workflow.compile()


def run_agent(
    user_input: str,
    messages: list[dict],
    system_prompt: str = "",
    session_id: str = "",
) -> tuple[str, list[dict]]:
    """运行 Agent，返回 (final_answer, updated_messages)。"""
    graph = build_graph()

    initial_state = {
        "messages": messages + [{"role": "user", "content": user_input}],
        "step_count": 0,
        "max_steps": settings.MAX_STEPS,
        "is_complete": False,
        "error_message": "",
        "final_answer": "",
        "session_id": session_id,
        "_system_prompt": system_prompt,
    }

    # 执行图
    final_state = graph.invoke(initial_state)

    answer = final_state.get("final_answer", "")
    updated_messages = list(final_state.get("messages", []))

    return answer, updated_messages
