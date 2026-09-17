"""LLM 调用封装：自动识别 Anthropic / OpenAI 兼容格式。"""

import json
from config import settings


def _is_anthropic_format() -> bool:
    """判断是否使用 Anthropic 格式（URL 含 anthropic）。"""
    return "anthropic" in settings.LLM_BASE_URL.lower()


def chat(
    messages: list[dict],
    system: str = "",
    tools: list[dict] | None = None,
    max_tokens: int = 4096,
) -> dict:
    """调用 LLM，自动选择 Anthropic 或 OpenAI 格式。"""
    if _is_anthropic_format():
        return _chat_anthropic(messages, system, tools, max_tokens)
    else:
        return _chat_openai(messages, system, tools, max_tokens)


# ── OpenAI 兼容格式（DeepSeek / MiMo OpenAI / 通义）──────────

def _chat_openai(messages, system, tools, max_tokens):
    from openai import OpenAI

    client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)

    api_messages = []
    if system:
        api_messages.append({"role": "system", "content": system})
    api_messages.extend(messages)

    kwargs = {"model": settings.LLM_MODEL, "messages": api_messages, "max_tokens": max_tokens}
    if tools:
        kwargs["tools"] = _format_tools_openai(tools)
        kwargs["tool_choice"] = "auto"

    response = client.chat.completions.create(**kwargs)
    return _parse_openai_response(response)


def _format_tools_openai(tools):
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("parameters", {"type": "object", "properties": {}}),
            },
        }
        for t in tools
    ]


def _parse_openai_response(response):
    choice = response.choices[0]
    message = choice.message

    result = {"stop_reason": choice.finish_reason, "text": message.content or "", "tool_calls": []}

    if message.tool_calls:
        for tc in message.tool_calls:
            result["tool_calls"].append({
                "id": tc.id,
                "name": tc.function.name,
                "args": json.loads(tc.function.arguments),
            })

    return result


# ── Anthropic 格式（MiMo Anthropic / Claude）──────────────

def _chat_anthropic(messages, system, tools, max_tokens):
    import anthropic

    client = anthropic.Anthropic(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
    )

    kwargs = {
        "model": settings.LLM_MODEL,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if system:
        kwargs["system"] = system
    if tools:
        kwargs["tools"] = _format_tools_anthropic(tools)

    response = client.messages.create(**kwargs)
    return _parse_anthropic_response(response)


def _format_tools_anthropic(tools):
    return [
        {
            "name": t["name"],
            "description": t.get("description", ""),
            "input_schema": t.get("parameters", {"type": "object", "properties": {}}),
        }
        for t in tools
    ]


def _parse_anthropic_response(response):
    result = {"stop_reason": response.stop_reason, "text": "", "tool_calls": []}

    for block in response.content:
        if block.type == "text":
            result["text"] += block.text
        elif block.type == "tool_use":
            result["tool_calls"].append({
                "id": block.id,
                "name": block.name,
                "args": block.input,
            })

    return result
