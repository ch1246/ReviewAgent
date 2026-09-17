"""代码搜索和目录列表工具。"""

import subprocess
import platform
from pathlib import Path
from tools.base import tool


@tool(
    name="search_code",
    description="在项目中搜索代码（使用 ripgrep 或 grep）。返回匹配的文件、行号和内容。",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "搜索模式（支持正则表达式）"},
            "path": {"type": "string", "description": "搜索目录，默认当前目录"},
            "file_type": {"type": "string", "description": "文件类型过滤，如 py、js、ts"},
        },
        "required": ["pattern"],
    },
)
def search_code(pattern: str, path: str = ".", file_type: str = "") -> str:
    # 优先用 ripgrep，没有则用 grep
    rg_cmd = _build_search_command(pattern, path, file_type)

    try:
        result = subprocess.run(
            rg_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return "搜索超时（30秒）"
    except Exception as e:
        return f"搜索失败：{e}"

    if result.returncode != 0 and not result.stdout:
        return f"未找到匹配：{pattern}"

    output = result.stdout
    if len(output) > 10000:
        output = output[:10000] + f"\n...（结果被截断）"

    return output if output else f"未找到匹配：{pattern}"


def _build_search_command(pattern: str, path: str, file_type: str) -> str:
    """构建搜索命令，优先 ripgrep。"""
    # 检查 ripgrep 是否可用
    rg_available = _command_exists("rg")

    if rg_available:
        cmd = f"rg -n --no-heading"
        if file_type:
            cmd += f" -t {file_type}"
        cmd += f' "{pattern}" {path}'
    else:
        # fallback to find + grep
        if file_type:
            cmd = f'find {path} -name "*.{file_type}" -exec grep -Hn "{pattern}" {{}} \\;'
        else:
            cmd = f'grep -rn "{pattern}" {path}'

    return cmd


def _command_exists(cmd: str) -> bool:
    try:
        if platform.system() == "Windows":
            subprocess.run(f"where {cmd}", shell=True, capture_output=True, check=True)
        else:
            subprocess.run(f"which {cmd}", shell=True, capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, Exception):
        return False


@tool(
    name="list_files",
    description="列出目录内容。支持递归列出。",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "目录路径，默认当前目录"},
            "recursive": {"type": "boolean", "description": "是否递归列出，默认 false"},
        },
        "required": [],
    },
)
def list_files(path: str = ".", recursive: bool = False) -> str:
    p = Path(path)
    if not p.exists():
        return f"错误：路径不存在 {path}"
    if not p.is_dir():
        return f"错误：不是目录 {path}"

    lines = []
    max_items = 200

    if recursive:
        for i, item in enumerate(p.rglob("*")):
            if i >= max_items:
                lines.append(f"...（结果被截断，共 {max_items}+ 项）")
                break
            rel = item.relative_to(p)
            prefix = "  " * len(rel.parts)
            name = rel.name + ("/" if item.is_dir() else "")
            lines.append(f"{prefix}{name}")
    else:
        for item in sorted(p.iterdir()):
            name = item.name + ("/" if item.is_dir() else "")
            lines.append(name)

    if not lines:
        return f"{path} 是空目录"

    header = f"目录：{path}\n"
    return header + "\n".join(lines)
