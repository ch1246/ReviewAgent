"""PushPlus 微信推送工具。"""

import requests
from tools.base import tool
from config import settings


PUSHPLUS_API = "https://www.pushplus.plus/send"


@tool(
    name="push_wechat",
    description="通过 PushPlus 推送消息到微信。支持 Markdown 格式。",
    parameters={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "消息标题"},
            "content": {"type": "string", "description": "消息内容（支持 Markdown）"},
            "template": {"type": "string", "description": "模板类型：txt/html/json/markdown，默认 markdown"},
        },
        "required": ["title", "content"],
    },
)
def push_wechat(title: str, content: str, template: str = "markdown") -> str:
    token = settings.PUSHPLUS_TOKEN
    if not token:
        return "错误：未配置 PUSHPLUS_TOKEN，请在 .env 文件中设置"

    data = {
        "token": token,
        "title": title,
        "content": content,
        "template": template,
    }

    try:
        resp = requests.post(PUSHPLUS_API, json=data, timeout=30)
        result = resp.json()

        if result.get("code") == 200:
            return "推送成功"
        else:
            return f"推送失败：{result.get('msg', '未知错误')}"

    except requests.Timeout:
        return "推送超时"
    except Exception as e:
        return f"推送出错：{e}"
