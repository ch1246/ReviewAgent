-- AI Agent 项目记忆数据库

CREATE DATABASE IF NOT EXISTS aiagent DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE aiagent;

-- 项目记忆主表
CREATE TABLE IF NOT EXISTS project_memory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_path VARCHAR(512) NOT NULL UNIQUE,
    project_name VARCHAR(255),
    framework VARCHAR(100) COMMENT '框架：FastAPI/Flask/Django 等',
    language VARCHAR(50) COMMENT '主语言：python/typescript 等',
    package_manager VARCHAR(50) COMMENT '包管理器：pip/poetry/npm 等',
    database_type VARCHAR(50) COMMENT '使用的数据库',
    code_style JSON COMMENT '代码风格约定',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_project_path (project_path)
) ENGINE=InnoDB;

-- 历史审查记录
CREATE TABLE IF NOT EXISTS project_issues (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    file_path VARCHAR(512),
    line_number INT,
    issue_type VARCHAR(50) COMMENT '问题类型：security/style/performance/bug',
    severity VARCHAR(20) COMMENT '严重程度：critical/high/medium/low',
    description TEXT,
    fix_description TEXT COMMENT '修复方式',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES project_memory(id) ON DELETE CASCADE,
    INDEX idx_project_id (project_id),
    INDEX idx_issue_type (issue_type)
) ENGINE=InnoDB;

-- 项目备注/用户偏好
CREATE TABLE IF NOT EXISTS project_notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    category VARCHAR(50) COMMENT '分类：preference/pitfall/convention',
    content TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES project_memory(id) ON DELETE CASCADE,
    INDEX idx_project_id (project_id)
) ENGINE=InnoDB;
