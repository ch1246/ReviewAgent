"""代码审查核心逻辑。"""

from pathlib import Path
from core.llm import chat
from reviewer.scorer import calculate_score
from memory.project_memory import get_memory_summary, add_issue


REVIEW_SYSTEM_PROMPT = """你是一个代码审查专家。根据提供的 diff 内容，找出代码问题。

对于每个问题，输出 JSON 格式：
```json
[
  {
    "file": "文件路径",
    "line": 行号,
    "dimension": "style|security|logic|performance|best_practice",
    "severity": "critical|high|medium|low",
    "description": "问题描述",
    "fix": "修复建议"
  }
]
```

审查维度：
- style：代码规范（命名、import、格式）
- security：安全漏洞（注入、XSS、硬编码密钥）
- logic：逻辑问题（空指针、边界条件、异常处理）
- performance：性能问题（N+1、内存泄漏、重复计算）
- best_practice：最佳实践（DRY、函数长度、魔法数字）

规则：
- 只报告真实问题，不要报告风格偏好
- severity 说明：critical=必须修复才能运行 / high=强烈建议修复 / medium=建议修复 / low=可选修复
- 如果没有问题，返回空数组 []
- 输出纯 JSON，不要其他文字"""


def review_diff(diff_text: str, project_path: str = "") -> dict:
    """
    审查 diff 内容。

    返回: {"issues": [...], "score": {...}, "diff_summary": "..."}
    """
    if not diff_text or diff_text == "没有变更":
        return {
            "issues": [],
            "score": calculate_score([]),
            "diff_summary": "没有代码变更",
        }

    # 截断过长的 diff
    if len(diff_text) > 20000:
        diff_text = diff_text[:20000] + "\n...(diff 被截断)"

    # 构造 prompt
    user_prompt = f"请审查以下代码变更：\n\n```diff\n{diff_text}\n```"

    # 如果有项目记忆，加入上下文
    if project_path:
        try:
            memory_summary = get_memory_summary(project_path)
            user_prompt = f"项目背景：\n{memory_summary}\n\n{user_prompt}"
        except Exception:
            pass  # 记忆获取失败不影响审查

    # 调用 LLM 审查
    try:
        response = chat(
            messages=[{"role": "user", "content": user_prompt}],
            system=REVIEW_SYSTEM_PROMPT,
            max_tokens=4096,
        )
    except Exception as e:
        return {
            "issues": [],
            "score": calculate_score([]),
            "diff_summary": f"审查失败：{e}",
        }

    # 解析结果
    issues = _parse_issues(response["text"])

    # 计算评分
    score = calculate_score(issues)

    # 记录问题到项目记忆
    if project_path and issues:
        for issue in issues:
            try:
                add_issue(
                    project_path=project_path,
                    file_path=issue.get("file", ""),
                    line_number=issue.get("line", 0),
                    issue_type=issue.get("dimension", "style"),
                    severity=issue.get("severity", "medium"),
                    description=issue.get("description", ""),
                    fix_description=issue.get("fix", ""),
                )
            except Exception:
                pass

    return {
        "issues": issues,
        "score": score,
        "diff_summary": f"发现 {len(issues)} 个问题",
    }


def _parse_issues(text: str) -> list[dict]:
    """从 LLM 输出中解析问题列表。"""
    import json
    import re

    # 尝试提取 JSON
    # 先找 ```json ... ```
    json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if json_match:
        text = json_match.group(1)
    else:
        # 尝试直接解析
        text = text.strip()
        # 如果开头不是 [，找第一个 [
        idx = text.find("[")
        if idx >= 0:
            text = text[idx:]
        # 找最后一个 ]
        idx = text.rfind("]")
        if idx >= 0:
            text = text[:idx + 1]

    try:
        issues = json.loads(text)
        if isinstance(issues, list):
            return issues
    except json.JSONDecodeError:
        pass

    return []
