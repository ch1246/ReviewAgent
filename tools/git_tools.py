"""Git 工具：获取变更内容。"""

import subprocess
from tools.base import tool


@tool(
    name="git_diff",
    description="获取 Git 变更内容。返回变更文件列表和 diff。",
    parameters={
        "type": "object",
        "properties": {
            "base_ref": {"type": "string", "description": "基准 commit，默认 HEAD~1"},
            "head_ref": {"type": "string", "description": "目标 commit，默认当前工作区"},
            "staged": {"type": "boolean", "description": "是否只看暂存区变更，默认 false"},
        },
        "required": [],
    },
)
def git_diff(base_ref: str = "", head_ref: str = "", staged: bool = False) -> str:
    try:
        if staged:
            cmd = "git diff --cached"
        elif base_ref and head_ref:
            cmd = f"git diff {base_ref}...{head_ref}"
        elif base_ref:
            cmd = f"git diff {base_ref}"
        else:
            cmd = "git diff HEAD"

        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )

        if result.returncode != 0:
            return f"git diff 失败：{result.stderr}"

        output = result.stdout
        if not output:
            return "没有变更"

        if len(output) > 15000:
            output = output[:15000] + "\n...（diff 被截断）"

        return output

    except subprocess.TimeoutExpired:
        return "git diff 超时"
    except Exception as e:
        return f"git diff 出错：{e}"


@tool(
    name="git_status",
    description="获取 Git 工作区状态（变更文件列表）。",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
def git_status() -> str:
    try:
        result = subprocess.run(
            "git status --short", shell=True, capture_output=True, text=True, timeout=10
        )
        return result.stdout if result.stdout else "工作区干净"
    except Exception as e:
        return f"git status 出错：{e}"


@tool(
    name="git_log",
    description="查看最近的 Git 提交记录。",
    parameters={
        "type": "object",
        "properties": {
            "count": {"type": "integer", "description": "显示条数，默认 10"},
        },
        "required": [],
    },
)
def git_log(count: int = 10) -> str:
    try:
        result = subprocess.run(
            f"git log --oneline -{count}",
            shell=True, capture_output=True, text=True, timeout=10,
        )
        return result.stdout if result.stdout else "没有提交记录"
    except Exception as e:
        return f"git log 出错：{e}"
