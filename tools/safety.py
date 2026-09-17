"""安全检查：命令黑名单、敏感文件保护。"""

import re

# 危险命令黑名单（正则匹配）
BLOCKED_COMMANDS = [
    r"\brm\s+(-[rf]+\s+)?/",          # rm -rf / 或 rm /
    r"\bmkfs\b",                        # 格式化磁盘
    r"\bformat\b",                      # 格式化
    r"\bdd\s+.*of=/dev/",              # dd 写磁盘
    r"\b:(){ :\|:& };:",               # fork bomb
    r"\bchmod\s+777\s+/",              # 全盘 777
    r"\bshutdown\b",
    r"\breboot\b",
    r"\binit\s+0\b",
]

# 敏感文件模式
SENSITIVE_PATTERNS = [
    r"\.env$",
    r"\.env\.",
    r"\.key$",
    r"\.pem$",
    r"\.p12$",
    r"\.pfx$",
    r"id_rsa",
    r"id_ed25519",
    r"\.secret$",
    r"credentials",
    r"token\.json",
]


def check_command(command: str) -> tuple[bool, str]:
    """检查命令是否安全。返回 (is_safe, reason)。"""
    for pattern in BLOCKED_COMMANDS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"危险命令被拦截：匹配规则 {pattern}"
    return True, ""


def check_file_path(path: str) -> tuple[bool, str]:
    """检查文件路径是否敏感。返回 (is_safe, reason)。"""
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, path, re.IGNORECASE):
            return False, f"敏感文件被拦截：{path} 匹配规则 {pattern}"
    return True, ""
