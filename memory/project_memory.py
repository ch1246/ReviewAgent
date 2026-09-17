"""MySQL 项目级长期记忆。"""

import json
import hashlib
from pathlib import Path
import pymysql
from config import settings


def get_connection() -> pymysql.Connection:
    return pymysql.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database=settings.MYSQL_DATABASE,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def _hash_path(path: str) -> str:
    return hashlib.md5(path.encode()).hexdigest()[:12]


def get_or_create_project(project_path: str) -> dict:
    """获取项目记忆，不存在则扫描创建。"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM project_memory WHERE project_path = %s",
                (project_path,),
            )
            row = cur.fetchone()
            if row:
                return row

            # 不存在 → 扫描项目并创建
            info = _scan_project(project_path)
            cur.execute(
                """INSERT INTO project_memory
                   (project_path, project_name, framework, language, package_manager, database_type, code_style)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (
                    project_path,
                    info["project_name"],
                    info["framework"],
                    info["language"],
                    info["package_manager"],
                    info["database_type"],
                    json.dumps(info["code_style"], ensure_ascii=False),
                ),
            )
            cur.execute(
                "SELECT * FROM project_memory WHERE project_path = %s",
                (project_path,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def _scan_project(project_path: str) -> dict:
    """扫描项目目录，提取基本信息。"""
    p = Path(project_path)
    info = {
        "project_name": p.name,
        "framework": "unknown",
        "language": "unknown",
        "package_manager": "unknown",
        "database_type": "unknown",
        "code_style": {},
    }

    # 检测语言和包管理器
    if (p / "requirements.txt").exists() or (p / "pyproject.toml").exists():
        info["language"] = "python"
        if (p / "pyproject.toml").exists():
            info["package_manager"] = "poetry"
        else:
            info["package_manager"] = "pip"
    elif (p / "package.json").exists():
        info["language"] = "javascript/typescript"
        info["package_manager"] = "npm"

    # 检测框架
    files = [f.name for f in p.rglob("*.py")] if info["language"] == "python" else []
    if "manage.py" in files:
        info["framework"] = "django"
    elif any("fastapi" in str(f) for f in p.rglob("*.py")):
        info["framework"] = "fastapi"

    # 检查 requirements.txt 中的框架
    req_file = p / "requirements.txt"
    if req_file.exists():
        content = req_file.read_text(encoding="utf-8").lower()
        if "fastapi" in content:
            info["framework"] = "fastapi"
        elif "flask" in content:
            info["framework"] = "flask"
        elif "django" in content:
            info["framework"] = "django"

        # 检测数据库
        if "pymysql" in content or "mysqlclient" in content:
            info["database_type"] = "mysql"
        elif "psycopg2" in content:
            info["database_type"] = "postgresql"
        elif "sqlite" in content:
            info["database_type"] = "sqlite"
        elif "redis" in content:
            info["database_type"] = "redis"

    return info


def update_code_style(project_path: str, style: dict):
    """更新项目代码风格。"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE project_memory SET code_style = %s WHERE project_path = %s",
                (json.dumps(style, ensure_ascii=False), project_path),
            )
    finally:
        conn.close()


def add_issue(project_path: str, file_path: str, line_number: int,
              issue_type: str, severity: str, description: str, fix_description: str = ""):
    """记录审查发现的问题。"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM project_memory WHERE project_path = %s", (project_path,))
            row = cur.fetchone()
            if not row:
                return
            project_id = row["id"]

            cur.execute(
                """INSERT INTO project_issues
                   (project_id, file_path, line_number, issue_type, severity, description, fix_description)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (project_id, file_path, line_number, issue_type, severity, description, fix_description),
            )
    finally:
        conn.close()


def get_recent_issues(project_path: str, limit: int = 10) -> list[dict]:
    """获取项目最近的审查问题。"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT pi.* FROM project_issues pi
                   JOIN project_memory pm ON pi.project_id = pm.id
                   WHERE pm.project_path = %s
                   ORDER BY pi.created_at DESC
                   LIMIT %s""",
                (project_path, limit),
            )
            return cur.fetchall()
    finally:
        conn.close()


def add_note(project_path: str, category: str, content: str):
    """添加项目备注。"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM project_memory WHERE project_path = %s", (project_path,))
            row = cur.fetchone()
            if not row:
                return
            cur.execute(
                "INSERT INTO project_notes (project_id, category, content) VALUES (%s, %s, %s)",
                (row["id"], category, content),
            )
    finally:
        conn.close()


def get_notes(project_path: str) -> list[dict]:
    """获取项目所有备注。"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT pn.* FROM project_notes pn
                   JOIN project_memory pm ON pn.project_id = pm.id
                   WHERE pm.project_path = %s
                   ORDER BY pn.created_at DESC""",
                (project_path,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_memory_summary(project_path: str) -> str:
    """获取项目记忆摘要（供 LLM 使用）。"""
    project = get_or_create_project(project_path)
    issues = get_recent_issues(project_path, 5)
    notes = get_notes(project_path)

    lines = [f"项目：{project['project_name']}"]
    lines.append(f"语言：{project['language']}，框架：{project['framework']}，数据库：{project['database_type']}")

    if issues:
        lines.append(f"\n最近审查发现的问题（{len(issues)} 个）：")
        for i in issues:
            lines.append(f"  - [{i['severity']}] {i['file_path']}:{i['line_number']} - {i['description']}")

    if notes:
        lines.append(f"\n项目备注：")
        for n in notes:
            lines.append(f"  - [{n['category']}] {n['content']}")

    return "\n".join(lines)
