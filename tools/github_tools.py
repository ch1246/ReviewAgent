"""GitHub 工具：PR 评论。自动从 git remote 检测仓库。"""

import re
import subprocess
import requests
from tools.base import tool
from config import settings


def _detect_repo() -> str:
    """从 git remote 自动检测 GitHub 仓库（owner/repo）。"""
    # 1. 先看 .env 配置
    if settings.GITHUB_REPO:
        return settings.GITHUB_REPO

    # 2. 从 git remote 检测
    try:
        result = subprocess.run(
            "git remote get-url origin",
            shell=True, capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            # 支持多种格式：
            # https://github.com/owner/repo.git
            # git@github.com:owner/repo.git
            # https://github.com/owner/repo
            match = re.search(r"github\.com[:/](.+?/.+?)(?:\.git)?$", url)
            if match:
                return match.group(1)
    except Exception:
        pass

    return ""


def _get_token() -> str:
    """获取 GitHub Token。"""
    return settings.GITHUB_TOKEN


@tool(
    name="github_comment",
    description="在 GitHub PR 上发评论。自动从 git remote 检测仓库，也可手动指定 repo。",
    parameters={
        "type": "object",
        "properties": {
            "pr_number": {"type": "integer", "description": "PR 编号"},
            "body": {"type": "string", "description": "评论内容（支持 Markdown）"},
            "repo": {"type": "string", "description": "仓库（owner/repo），不填自动检测"},
        },
        "required": ["pr_number", "body"],
    },
)
def github_comment(pr_number: int, body: str, repo: str = "") -> str:
    token = _get_token()
    if not token:
        return "错误：未配置 GITHUB_TOKEN，请在 .env 文件中设置"

    repo = repo or _detect_repo()
    if not repo:
        return "错误：无法检测仓库。请在 .env 中配置 GITHUB_REPO，或确保当前目录是 GitHub 仓库"

    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {"body": body}

    try:
        resp = requests.post(url, json=data, headers=headers, timeout=30)
        if resp.status_code == 201:
            comment_url = resp.json().get("html_url", "")
            return f"评论已发布：{comment_url}"
        else:
            return f"评论失败：{resp.status_code} - {resp.text[:500]}"
    except Exception as e:
        return f"评论请求失败：{e}"


@tool(
    name="github_list_prs",
    description="列出 GitHub 仓库的最近 PR。自动从 git remote 检测仓库。",
    parameters={
        "type": "object",
        "properties": {
            "state": {"type": "string", "description": "PR 状态：open/closed/all，默认 open"},
            "repo": {"type": "string", "description": "仓库（owner/repo），不填自动检测"},
        },
        "required": [],
    },
)
def github_list_prs(state: str = "open", repo: str = "") -> str:
    token = _get_token()
    if not token:
        return "错误：未配置 GITHUB_TOKEN"

    repo = repo or _detect_repo()
    if not repo:
        return "错误：无法检测仓库"

    url = f"https://api.github.com/repos/{repo}/pulls"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    params = {"state": state, "sort": "updated", "direction": "desc", "per_page": 10}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code != 200:
            return f"查询失败：{resp.status_code}"

        prs = resp.json()
        if not prs:
            return f"没有 {state} 状态的 PR"

        lines = []
        for pr in prs:
            lines.append(f"#{pr['number']} [{pr['state']}] {pr['title']} - {pr['user']['login']}")
        return "\n".join(lines)
    except Exception as e:
        return f"查询失败：{e}"
