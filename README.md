# ReviewAgent - 代码审查助手

基于 LLM 的代码助手，支持交互对话和自动代码审查。

## 功能

- **交互模式**：自然语言对话，读写文件、执行命令、搜索代码
- **自动审查**：git push 时自动审查代码，评分后推送到 GitHub + 微信
- **项目记忆**：每个项目独立记忆，记住框架、风格、历史问题

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key
```

### 3. 初始化数据库（可选，需要项目记忆功能）

```bash
mysql -u root -p < db/schema.sql
```

### 4. 运行

**交互模式**：
```bash
python main.py
```

**手动运行审查**：
```bash
python review.py
```

**安装 Git hook（自动审查）**：
```bash
bash install_hook.sh /path/to/your/project
```

## 配置说明

| 变量 | 说明 | 必填 |
|------|------|------|
| LLM_API_KEY | LLM API 密钥 | 是 |
| LLM_BASE_URL | API 地址 | 是 |
| LLM_MODEL | 模型名称 | 是 |
| REDIS_HOST | Redis 地址 | 否（默认 localhost） |
| MYSQL_* | MySQL 配置 | 否（项目记忆功能需要） |
| GITHUB_TOKEN | GitHub Token | 否（PR 评论需要） |
| PUSHPLUS_TOKEN | PushPlus Token | 否（微信推送需要） |

## 支持的 LLM

- DeepSeek（默认）
- MiMo
- 通义千问
- 其他 OpenAI 兼容 API

在 `.env` 中切换：
```bash
# DeepSeek
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

# MiMo
LLM_BASE_URL=https://api.mimo.ai/v1
LLM_MODEL=mimo-chat
```
