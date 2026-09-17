"""Shell 命令执行工具。"""

import subprocess
import platform
from tools.base import tool
from tools.safety import check_command
from config import settings


@tool(
    name="run_command",
    description="执行 shell 命令并返回输出。支持超时控制和输出截断。",
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "要执行的命令"},
            "timeout": {"type": "integer", "description": "超时秒数，默认30秒"},
        },
        "required": ["command"],
    },
)
def run_command(command: str, timeout: int = 0) -> str:
    if timeout <= 0:
        timeout = settings.COMMAND_TIMEOUT

    safe, reason = check_command(command)
    if not safe:
        return reason

    # Windows 用 cmd，其他用 shell
    use_shell = True
    if platform.system() == "Windows":
        shell_cmd = command
    else:
        shell_cmd = command

    try:
        result = subprocess.run(
            shell_cmd,
            shell=use_shell,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=None,
        )
    except subprocess.TimeoutExpired:
        return f"命令超时（{timeout}秒）：{command}"
    except Exception as e:
        return f"命令执行失败：{e}"

    output_parts = []

    if result.stdout:
        stdout = result.stdout
        if len(stdout) > 10000:
            stdout = stdout[:10000] + f"\n...（输出被截断，共 {len(result.stdout)} 字符）"
        output_parts.append(stdout)

    if result.stderr:
        stderr = result.stderr
        if len(stderr) > 5000:
            stderr = stderr[:5000] + f"\n...（错误输出被截断）"
        output_parts.append(f"[stderr]\n{stderr}")

    if result.returncode != 0:
        output_parts.append(f"[退出码] {result.returncode}")

    if not output_parts:
        return "命令执行成功（无输出）"

    return "\n".join(output_parts)
