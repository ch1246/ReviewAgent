"""上下文压缩：对话历史过长时生成摘要。"""

from core.llm import chat
from config import settings


def compress_messages(messages: list[dict], max_tokens: int = 0) -> list[dict]:
    """压缩对话历史。保留系统消息 + 最近 N 轮 + 早期消息摘要。"""
    if max_tokens <= 0:
        max_tokens = settings.CONTEXT_MAX_TOKENS

    # 粗略估算 token（1 中文字 ≈ 2 tokens）
    total_chars = sum(len(str(m.get("content", ""))) for m in messages)
    estimated_tokens = total_chars * 1.5

    if estimated_tokens <= max_tokens:
        return messages  # 不需要压缩

    # 保留：最近 6 条消息（3 轮对话）
    recent_count = 6
    if len(messages) <= recent_count:
        return messages

    recent = messages[-recent_count:]
    early = messages[:-recent_count]

    if not early:
        return recent

    # 把早期消息压缩成摘要
    summary = _summarize(early)

    # 组合：摘要 + 最近消息
    summary_msg = {
        "role": "user",
        "content": f"[历史对话摘要]\n{summary}",
    }
    summary_reply = {
        "role": "assistant",
        "content": "好的，我已了解历史对话内容。",
    }

    return [summary_msg, summary_reply] + recent


def _summarize(messages: list[dict]) -> str:
    """用 LLM 把消息压缩成摘要。"""
    # 提取消息文本
    texts = []
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, str):
            texts.append(f"[{m['role']}]: {content}")
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        texts.append(f"[{m['role']}]: {block['text']}")
                    elif block.get("type") == "tool_use":
                        texts.append(f"[{m['role']}]: 调用工具 {block.get('name', '')}")
                    elif block.get("type") == "tool_result":
                        texts.append(f"[{m['role']}]: 工具结果")

    conversation = "\n".join(texts)

    # 截断避免摘要本身太长
    if len(conversation) > 8000:
        conversation = conversation[:8000] + "\n...(截断)"

    try:
        response = chat(
            messages=[{"role": "user", "content": f"请将以下对话压缩为简短摘要（200字以内），保留关键信息：\n\n{conversation}"}],
            system="你是一个对话摘要助手，擅长提取关键信息。",
            max_tokens=500,
        )
        return response["text"]
    except Exception:
        # 摘要失败，简单截断
        return f"（历史对话共 {len(messages)} 条消息，已省略）"
