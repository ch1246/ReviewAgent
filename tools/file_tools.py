"""文件操作工具：读取、写入、编辑文件。"""

from pathlib import Path
from tools.base import tool
from tools.safety import check_file_path


@tool(
    name="read_file",
    description="读取文件内容。支持指定行范围。返回文件内容和行号。",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径（相对或绝对路径）"},
            "offset": {"type": "integer", "description": "起始行号（从0开始），不填则从头读"},
            "limit": {"type": "integer", "description": "读取行数，不填则读全部（最多500行）"},
        },
        "required": ["path"],
    },
)
def read_file(path: str, offset: int = 0, limit: int = 500) -> str:
    safe, reason = check_file_path(path)
    if not safe:
        return reason

    p = Path(path)
    if not p.exists():
        return f"错误：文件不存在 {path}"
    if not p.is_file():
        return f"错误：不是文件 {path}"

    try:
        lines = p.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return f"错误：无法读取 {path}（可能是二进制文件）"

    total = len(lines)
    selected = lines[offset:offset + limit]

    result_lines = []
    for i, line in enumerate(selected, start=offset + 1):
        result_lines.append(f"{i:4d} | {line}")

    header = f"文件：{path}（共 {total} 行，显示 {offset + 1}~{offset + len(selected)} 行）\n"
    return header + "\n".join(result_lines)


@tool(
    name="write_file",
    description="写入文件。如果文件已存在则覆盖。会自动创建不存在的目录。",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "content": {"type": "string", "description": "要写入的内容"},
        },
        "required": ["path", "content"],
    },
)
def write_file(path: str, content: str) -> str:
    safe, reason = check_file_path(path)
    if not safe:
        return reason

    p = Path(path)
    existed = p.exists()

    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    except Exception as e:
        return f"写入失败：{e}"

    if existed:
        return f"已覆盖写入 {path}（{len(content)} 字符）"
    else:
        return f"已创建文件 {path}（{len(content)} 字符）"


@tool(
    name="edit_file",
    description="局部编辑文件：将文件中的 old_str 替换为 new_str。old_str 必须在文件中唯一存在。",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "old_str": {"type": "string", "description": "要替换的原文（必须唯一匹配）"},
            "new_str": {"type": "string", "description": "替换后的内容"},
        },
        "required": ["path", "old_str", "new_str"],
    },
)
def edit_file(path: str, old_str: str, new_str: str) -> str:
    safe, reason = check_file_path(path)
    if not safe:
        return reason

    p = Path(path)
    if not p.exists():
        return f"错误：文件不存在 {path}"

    try:
        content = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"错误：无法读取 {path}（可能是二进制文件）"

    count = content.count(old_str)
    if count == 0:
        return f"错误：在 {path} 中未找到匹配内容"
    if count > 1:
        return f"错误：在 {path} 中找到 {count} 处匹配，old_str 必须唯一。请提供更长的上下文。"

    new_content = content.replace(old_str, new_str, 1)
    p.write_text(new_content, encoding="utf-8")

    return f"已编辑 {path}：替换了一处内容"
