"""审查报告生成。"""

from reviewer.rules import REVIEW_DIMENSIONS


def format_github_report(review_result: dict) -> str:
    """格式化为 GitHub PR 评论。"""
    score = review_result["score"]
    issues = review_result["issues"]

    lines = []
    lines.append("## 📊 代码审查报告\n")
    lines.append(f"**评分：{score['total']} / 100**（{score['grade']}）")
    lines.append(f"**结论：{score['conclusion']}\n**")

    # 评分明细
    lines.append("### 评分明细\n")
    lines.append("| 维度 | 得分 | 权重 | 加权分 |")
    lines.append("|------|------|------|--------|")
    for dim_key, dim_data in score["breakdown"].items():
        lines.append(
            f"| {dim_data['name']} | {dim_data['score']} | {dim_data['weight']*100:.0f}% | {dim_data['weighted_score']} |"
        )

    # 问题列表
    if issues:
        lines.append(f"\n### 发现 {len(issues)} 个问题\n")
        for i, issue in enumerate(issues, 1):
            severity_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🔵",
            }.get(issue.get("severity", "medium"), "⚪")

            dim_name = REVIEW_DIMENSIONS.get(
                issue.get("dimension", "style"), {}
            ).get("name", issue.get("dimension", ""))

            lines.append(f"**{i}. {severity_emoji} [{dim_name}] {issue.get('file', '')}:{issue.get('line', '')}**")
            lines.append(f"   {issue.get('description', '')}")
            if issue.get("fix"):
                lines.append(f"   💡 建议：{issue['fix']}")
            lines.append("")
    else:
        lines.append("\n✅ 未发现问题，代码质量良好！")

    return "\n".join(lines)


def format_wechat_message(review_result: dict, project_name: str = "") -> str:
    """格式化为微信推送消息（简洁版）。"""
    score = review_result["score"]
    issues = review_result["issues"]

    lines = []
    lines.append("📊 代码审查报告\n")

    if project_name:
        lines.append(f"项目：{project_name}")

    lines.append(f"评分：{score['total']} / 100")
    lines.append(f"结论：{score['conclusion']}")

    if issues:
        # 按严重程度分组
        by_severity = {}
        for issue in issues:
            sev = issue.get("severity", "medium")
            by_severity.setdefault(sev, []).append(issue)

        severity_order = ["critical", "high", "medium", "low"]
        severity_labels = {
            "critical": "严重",
            "high": "高",
            "medium": "中",
            "low": "低",
        }

        lines.append(f"\n问题摘要（共 {len(issues)} 个）：")
        for sev in severity_order:
            if sev in by_severity:
                count = len(by_severity[sev])
                label = severity_labels.get(sev, sev)
                lines.append(f"  {label}风险：{count} 个")

        # 列出前 5 个问题
        lines.append("\n主要问题：")
        for i, issue in enumerate(issues[:5], 1):
            dim_name = REVIEW_DIMENSIONS.get(
                issue.get("dimension", "style"), {}
            ).get("name", "")
            lines.append(
                f"  {i}. [{dim_name}] {issue.get('file', '')}:{issue.get('line', '')} - {issue.get('description', '')}"
            )

        if len(issues) > 5:
            lines.append(f"  ...还有 {len(issues) - 5} 个问题")
    else:
        lines.append("\n✅ 未发现问题")

    return "\n".join(lines)


def format_local_report(review_result: dict, project_name: str = "") -> str:
    """格式化为本地文件报告。"""
    return format_github_report(review_result)
