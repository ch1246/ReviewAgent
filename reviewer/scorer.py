"""评分逻辑。"""

from reviewer.rules import REVIEW_DIMENSIONS, SEVERITY_PENALTY


def calculate_score(issues: list[dict]) -> dict:
    """
    计算审查评分。

    issues: [{"dimension": "security", "severity": "high", ...}, ...]

    返回: {"total": 85, "grade": "良好", "breakdown": {...}, "summary": "..."}
    """
    # 按维度统计扣分
    dimension_deductions = {dim: 0 for dim in REVIEW_DIMENSIONS}

    for issue in issues:
        dim = issue.get("dimension", "style")
        severity = issue.get("severity", "medium")
        penalty = SEVERITY_PENALTY.get(severity, 5)
        dimension_deductions[dim] = dimension_deductions.get(dim, 0) + penalty

    # 计算各维度得分（满分 100，按权重）
    breakdown = {}
    weighted_total = 0

    for dim_key, dim_info in REVIEW_DIMENSIONS.items():
        deduction = dimension_deductions.get(dim_key, 0)
        dim_score = max(0, 100 - deduction)
        weighted_score = dim_score * dim_info["weight"]
        weighted_total += weighted_score

        breakdown[dim_key] = {
            "name": dim_info["name"],
            "weight": dim_info["weight"],
            "score": dim_score,
            "weighted_score": round(weighted_score, 1),
            "deduction": deduction,
        }

    total = round(weighted_total)

    # 评级
    if total >= 90:
        grade = "优秀"
        conclusion = "可以运行，代码质量良好"
    elif total >= 70:
        grade = "良好"
        conclusion = "有需要关注的问题，建议修复后提交"
    elif total >= 60:
        grade = "及格"
        conclusion = "建议修复后再提交"
    else:
        grade = "不建议提交"
        conclusion = "有严重问题，必须修复"

    return {
        "total": total,
        "grade": grade,
        "conclusion": conclusion,
        "breakdown": breakdown,
    }
