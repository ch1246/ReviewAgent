"""审查模式入口：被 Git hook 调用，完成审查后推送到 GitHub + 微信。"""

import sys
import subprocess
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path

# 导入工具
import tools.git_tools
import tools.github_tools
import tools.push_tools

from tools.base import execute_tool
from reviewer.reviewer import review_diff
from reviewer.reporter import format_github_report, format_wechat_message, format_local_report
from tools.push_tools import push_wechat
from config import settings


def get_project_name() -> str:
    """获取当前项目名称。"""
    try:
        result = subprocess.run(
            "git rev-parse --show-toplevel",
            shell=True, capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()).name
    except Exception:
        pass
    return "unknown"


def get_diff() -> str:
    """获取待审查的 diff。"""
    # 优先看暂存区（有 add 的话）
    result = subprocess.run(
        "git diff --cached", shell=True, capture_output=True, text=True, timeout=10
    )
    if result.stdout:
        return result.stdout

    # 对比远程分支（pre-push 场景）
    result = subprocess.run(
        "git diff @{u}", shell=True, capture_output=True, text=True, timeout=10
    )
    if result.stdout:
        return result.stdout

    # 否则看工作区
    result = subprocess.run(
        "git diff HEAD", shell=True, capture_output=True, text=True, timeout=10
    )
    return result.stdout or ""


def get_project_path() -> str:
    """获取项目根目录。"""
    try:
        result = subprocess.run(
            "git rev-parse --show-toplevel",
            shell=True, capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "."


def run_review():
    """执行完整审查流程。"""
    print("🔍 开始代码审查...\n")

    # 1. 获取 diff
    diff = get_diff()
    if not diff:
        print("没有代码变更，跳过审查")
        return

    project_name = get_project_name()
    project_path = get_project_path()

    print(f"项目：{project_name}")
    print(f"Diff 大小：{len(diff)} 字符\n")

    # 2. 审查
    print("正在审查...")
    result = review_diff(diff, project_path=project_path)

    issues = result["issues"]
    score = result["score"]

    print(f"审查完成：{len(issues)} 个问题，评分 {score['total']}/100\n")

    # 3. 生成报告
    github_report = format_github_report(result)
    wechat_msg = format_wechat_message(result, project_name)
    local_report = format_local_report(result, project_name)

    # 4. 发送到 GitHub PR 评论（如果有 PR）
    from tools.github_tools import _detect_repo, _get_token
    repo = _detect_repo()
    if _get_token() and repo:
        pr_number = _get_current_pr_number()
        if pr_number:
            print(f"正在发送到 GitHub PR #{pr_number}（{repo}）...")
            from tools.base import execute_tool
            gh_result = execute_tool("github_comment", {
                "pr_number": pr_number,
                "body": github_report,
            })
            print(f"GitHub：{gh_result}")
        else:
            print("未找到关联的 PR，跳过 GitHub 评论")
    else:
        print("未配置 GITHUB_TOKEN 或无法检测仓库，跳过 GitHub 评论")

    # 5. 保存本地报告
    report_path = Path(project_path) / ".review_report.md"
    report_path.write_text(local_report, encoding="utf-8")
    print(f"本地报告：{report_path}")

    # 6. 推送到微信
    if settings.PUSHPLUS_TOKEN:
        print("正在推送到微信...")
        push_result = push_wechat(
            title=f"代码审查 - {project_name} ({score['total']}分)",
            content=wechat_msg,
        )
        print(f"微信：{push_result}")
    else:
        print("未配置 PUSHPLUS_TOKEN，跳过微信推送")

    # 7. 输出摘要
    print(f"\n{'='*40}")
    print(f"评分：{score['total']} / 100（{score['grade']}）")
    print(f"结论：{score['conclusion']}")
    if issues:
        print(f"问题：{len(issues)} 个")
        for i, issue in enumerate(issues[:5], 1):
            print(f"  {i}. [{issue.get('severity', '')}] {issue.get('file', '')}:{issue.get('line', '')} - {issue.get('description', '')}")
        if len(issues) > 5:
            print(f"  ...还有 {len(issues) - 5} 个问题")
    print(f"{'='*40}")


def _get_current_pr_number() -> int | None:
    """尝试获取当前分支关联的 PR 编号。"""
    try:
        from tools.github_tools import _detect_repo, _get_token
        repo = _detect_repo()
        token = _get_token()
        if not repo or not token:
            return None

        result = subprocess.run(
            "git rev-parse --abbrev-ref HEAD",
            shell=True, capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return None
        branch = result.stdout.strip()

        import requests
        url = f"https://api.github.com/repos/{repo}/pulls"
        headers = {"Authorization": f"token {token}"}
        params = {"head": f"{repo.split('/')[0]}:{branch}", "state": "open"}

        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            prs = resp.json()
            if prs:
                return prs[0]["number"]
    except Exception:
        pass
    return None


if __name__ == "__main__":
    run_review()
