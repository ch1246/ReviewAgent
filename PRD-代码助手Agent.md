# PRD：代码助手 Agent

## 1. 产品概述

### 1.1 产品定义

一个基于 LLM 的代码助手 Agent，支持两种使用方式：
1. **交互模式**：用户通过自然语言与 Agent 对话，Agent 读写文件、执行命令、搜索代码、分析问题并给出修复方案
2. **自动审查模式**：每次 push 到 GitHub 时自动触发代码审查，检查代码质量、安全漏洞、逻辑问题，审查结果自动写入 GitHub PR 评论或 Issue

定位为开发者本地使用的个人编程助手，兼顾日常交互和 push 时自动审查。

### 1.2 目标用户

- 本项目的开发者本人（主要用户）
- 有 Python 开发经验的中高级开发者
- 熟悉命令行操作

### 1.3 产品目标

| 优先级 | 目标 | 衡量标准 |
|--------|------|----------|
| P0 | 能实际修改代码文件，不是只给建议 | 用户说"把 print 换成 logging"，Agent 直接改文件 |
| P0 | 能执行命令并处理结果 | 跑测试、装依赖、看报错，Agent 自动处理 |
| P0 | push 到 GitHub 时自动代码审查 | git push 后自动审查变更代码，结果写入 PR 评论 |
| P1 | 多步任务自动编排 | "修复这个 bug" → 分析 → 定位 → 修复 → 验证，全自动 |
| P1 | 多轮对话理解上下文 | "刚才那个文件的第 10 行改成 xxx" 能理解"那个文件"是什么 |
| P1 | 项目级长期记忆 | 每个项目独立记忆，记住框架、风格、历史问题 |
| P2 | 代码质量分析 | 审查代码风格、安全漏洞、性能问题 |
| P2 | 参考项目现有代码风格 | 生成的代码风格与项目保持一致 |

### 1.4 非目标（本期不做）

- IDE 插件（不做 VS Code/JetBrains 集成）
- Web UI（先做命令行交互）
- 多用户/团队协作
- RAG 知识库（用户已做过，本期不重复）
- 自动 Git 提交（只审查和修改文件，不自动 commit）

### 1.5 两种使用模式

| 模式 | 触发方式 | 用途 |
|------|----------|------|
| 交互模式 | 运行 `python main.py` 启动对话 | 日常开发：读代码、改代码、跑命令、问问题 |
| 自动审查模式 | git push 后自动触发（Git hook） | 每次 push 自动审查变更代码，结果发到 GitHub |

---

## 2. 用户场景（User Stories）

### 场景 1：读取并分析代码

**用户**：帮我看看 main.py 有没有什么问题

**Agent 行为**：
1. 调用 read_file 读取 main.py 内容
2. 分析代码：语法、逻辑、风格、性能
3. 输出问题列表和修改建议

**验收标准**：Agent 能读取文件并给出有意义的分析，不是泛泛而谈

---

### 场景 2：批量代码修改

**用户**：把项目里所有 print 语句替换成 logging.info

**Agent 行为**：
1. 调用 search_code 搜索所有 print 语句
2. 逐个文件调用 edit_file 进行替换
3. 汇报修改了多少个文件、多少处

**验收标准**：确实改了文件，改对了，没有遗漏也没有误改

---

### 场景 3：生成新代码

**用户**：写一个 Redis 工具类，支持基本的 get/set/delete 操作，放到 utils/redis_client.py

**Agent 行为**：
1. 检查项目现有代码风格（import 方式、注释风格、类型标注）
2. 生成符合项目风格的 Redis 工具类
3. 写入指定路径
4. 如果目录不存在，先创建目录

**验收标准**：生成的代码能跑，风格与项目一致

---

### 场景 4：Bug 诊断与修复

**用户**：运行 main.py 报错了，帮我看看怎么回事

**Agent 行为**：
1. 调用 run_command 执行 main.py，捕获错误输出
2. 分析错误信息，定位问题文件和行号
3. 读取相关代码，分析根因
4. 调用 edit_file 修复代码
5. 再次运行验证修复成功

**验收标准**：能自动完成"运行 → 报错 → 分析 → 修复 → 验证"完整闭环

---

### 场景 5：多轮对话

**用户**：帮我看看 utils/helper.py
**Agent**：读取文件，分析，给出内容摘要和问题
**用户**：第 15 行那个函数参数类型不对，改一下
**Agent**：理解"那个函数"指的是第 15 行的函数，修改参数类型
**用户**：再加个异常处理
**Agent**：理解是接着改同一个函数，加上 try-except

**验收标准**：能正确理解上下文指代，不需要用户重复说明

---

### 场景 6：执行命令

**用户**：帮我装一下项目依赖

**Agent 行为**：
1. 检查项目根目录是否有 requirements.txt / pyproject.toml
2. 根据包管理器类型执行 pip install / poetry install
3. 输出安装结果

**验收标准**：能正确选择包管理器，执行命令，处理成功/失败

---

### 场景 7：代码搜索

**用户**：项目里哪些地方用了 requests 库？

**Agent 行为**：
1. 调用 search_code 搜索 "import requests" 和 "from requests"
2. 列出文件路径和行号
3. 简要说明每个地方的用途

**验收标准**：搜索结果准确，不遗漏

---

### 场景 8：审查结果推送到微信

**触发**：代码审查完成后自动触发

**Agent 行为**：
1. 审查完成，计算评分（满分 100）
2. 生成审查摘要：评分、问题数量、严重程度分布、是否能运行
3. 通过 PushPlus API 发送到用户微信

**推送消息格式**：

```
📊 代码审查报告

项目：aiagent
评分：85 / 100
结论：可以运行，有 2 个需要关注的问题

⚠️ 问题摘要：
  1. [安全] utils/db.py:42 - SQL 拼接，有注入风险
  2. [性能] core/agent.py:108 - 循环内重复创建连接
  3. [规范] tools/file_tools.py:15 - 未使用的 import

✅ 通过项：命名规范、异常处理、代码风格
```

**验收标准**：审查完自动推送到微信，消息格式清晰，有评分和简要结论

---

### 场景 9：Push 时自动代码审查

**触发**：用户执行 `git push` 到 GitHub

**Agent 行为**：
1. Git hook 触发 Agent
2. 获取本次 push 的变更文件列表（git diff）
3. 逐文件审查：代码规范、安全漏洞、逻辑问题、潜在 bug
4. 生成审查报告 + 评分（满分 100）
5. 通过 GitHub API 将报告写入对应的 PR 评论（如果有 PR）
6. 如果没有 PR，写入本地审查报告文件
7. 通过 PushPlus 推送评分和摘要到用户微信

**审查维度**：

| 维度 | 检查内容 | 权重 |
|------|----------|------|
| 代码规范 | 命名规范、import 顺序、未使用的变量、格式问题 | 20% |
| 安全漏洞 | SQL 注入、XSS、硬编码密钥、不安全的依赖 | 30% |
| 逻辑问题 | 空指针、边界条件、异常未处理、资源未释放 | 25% |
| 性能问题 | N+1 查询、不必要的循环、内存泄漏风险 | 15% |
| 最佳实践 | 是否符合项目已有的代码风格（参考长期记忆） | 10% |

**评分规则**：
- 满分 100 分，按维度权重加权
- 每个问题按严重程度扣分：严重 -10 / 中等 -5 / 轻微 -2
- 90+：优秀，可以运行
- 70~89：良好，有需要关注的问题
- 60~69：及格，建议修复后再提交
- < 60：不建议提交，有严重问题

**验收标准**：push 后自动审查，结果发到 GitHub + 微信，有评分和结论

---

### 场景 10：项目记忆积累

**场景**：用户在不同项目中使用 Agent，Agent 能记住每个项目的特点

**示例**：
- 项目 A：用 FastAPI + PostgreSQL，代码风格用 4 空格缩进，之前修复过连接池泄漏
- 项目 B：用 Flask + Redis，之前审查发现过 XSS 漏洞

**Agent 行为**：
1. 首次进入项目时，扫描项目结构、依赖、框架
2. 审查代码时，参考该项目的历史记忆
3. 每次交互后，自动更新项目记忆（新发现的模式、修过的 bug、用户偏好）

**验收标准**：切换项目后，Agent 能说出"这个项目之前用的是 FastAPI"，而不是当作新项目

---

## 3. 功能需求

### 3.1 核心工具集

| 工具 | 功能 | 输入 | 输出 | 风险等级 |
|------|------|------|------|----------|
| read_file | 读取文件内容 | path, offset?, limit? | 文件内容 | 低 |
| write_file | 写入/覆盖文件 | path, content | 成功/失败 | 高 |
| edit_file | 局部编辑文件 | path, old_str, new_str | 成功/失败 | 中 |
| run_command | 执行 shell 命令 | command, timeout? | stdout, stderr, exit_code | 高 |
| search_code | 搜索代码 | pattern, path?, file_type? | 匹配结果列表 | 低 |
| list_files | 列出目录内容 | path, recursive? | 文件/目录列表 | 低 |
| git_diff | 获取变更内容 | base_ref?, head_ref? | 变更文件列表 + diff 内容 | 低 |
| github_comment | 在 PR 上发评论 | repo, pr_number, body | 成功/失败 | 中 |
| push_wechat | 推送消息到微信 | title, content | 成功/失败 | 低 |

### 3.2 工具安全约束

| 工具 | 约束 |
|------|------|
| write_file | 写入前确认目标文件存在则提示用户；禁止写入 .env、密钥文件 |
| edit_file | old_str 必须唯一匹配，否则拒绝执行并提示 |
| run_command | 禁止执行 rm -rf /、格式化等危险命令；超时自动终止（默认 30s） |
| run_command | 长时间命令输出截断（最大 10000 字符） |

### 3.3 Agent 编排（LangGraph）

**状态定义**：

| 字段 | 类型 | 说明 |
|------|------|------|
| messages | 消息列表 | 完整对话历史 |
| tool_calls | 列表 | LLM 决定调用的工具 |
| tool_results | 列表 | 工具执行结果 |
| step_count | 整数 | 当前执行步数 |
| max_steps | 整数 | 最大步数限制（默认 15） |
| is_complete | 布尔 | 是否完成任务 |
| error_message | 字符串 | 错误信息 |
| final_answer | 字符串 | 最终回答 |

**节点**：

| 节点 | 职责 |
|------|------|
| agent | 调用 LLM，决定回答还是调工具 |
| tool_executor | 执行工具调用 |
| context_manager | 检查上下文长度，必要时压缩 |

**流转**：

```
agent → (需要工具?) → tool_executor → agent
  ↓ (不需要)
  END
```

**退出条件**：
- LLM 给出最终回答（不需要调工具）
- step_count >= max_steps
- 连续 3 次相同工具 + 相同参数（死循环检测）
- 总耗时超过 5 分钟

### 3.4 上下文管理

| 规则 | 说明 |
|------|------|
| 滑动窗口 | 保留最近 20 轮对话 |
| 摘要压缩 | 超过 20 轮时，早期对话压缩为摘要 |
| 文件内容截断 | 单次读取文件最大 500 行，超出部分提示用户指定范围 |
| 工具输出截断 | 单次工具输出最大 10000 字符 |

### 3.5 多轮对话

- 通过 session_id 隔离不同会话
- 支持上下文指代："那个文件"、"刚才的函数"、"第 10 行"
- 会话历史持久化到 Redis（TTL 24 小时）

### 3.6 记忆系统

**短期记忆**（Redis）：

| 数据 | Key | TTL |
|------|-----|-----|
| 对话历史 | chat:{session_id}:messages | 24h |
| 最近操作的文件 | chat:{session_id}:last_file | 24h |
| 最近执行的命令 | chat:{session_id}:last_command | 24h |

**长期记忆**（项目级，每个项目独立存储）：

| 数据 | 说明 | 存储方式 |
|------|------|----------|
| 项目元信息 | 框架、语言、包管理器、数据库 | JSON 文件，按项目路径隔离 |
| 代码风格约定 | 缩进、引号、命名规则、注释风格 | 从项目代码中自动学习 |
| 历史审查记录 | 之前审查发现过什么问题、修过什么 bug | JSON 文件，带时间戳 |
| 用户偏好 | 用户在该项目中的特殊要求 | JSON 文件 |
| 常见坑 | 该项目特有的注意事项 | JSON 文件 |

存储位置：MySQL 数据库

表结构设计：

**project_memory 表**（项目记忆主表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int, PK | 自增主键 |
| project_path | varchar | 项目路径（唯一索引） |
| project_name | varchar | 项目名称 |
| framework | varchar | 框架（FastAPI/Flask/Django 等） |
| language | varchar | 主语言 |
| package_manager | varchar | 包管理器（pip/poetry 等） |
| database | varchar | 使用的数据库 |
| code_style | json | 代码风格约定（缩进、引号、命名规则） |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 最后更新时间 |

**project_issues 表**（历史审查记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int, PK | 自增主键 |
| project_id | int, FK | 关联项目 |
| file_path | varchar | 文件路径 |
| line_number | int | 行号 |
| issue_type | varchar | 问题类型（security/style/performance/bug） |
| description | text | 问题描述 |
| fix_description | text | 修复方式 |
| created_at | datetime | 发现时间 |

**project_notes 表**（项目备注/用户偏好）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int, PK | 自增主键 |
| project_id | int, FK | 关联项目 |
| category | varchar | 分类（preference/pitfall/convention） |
| content | text | 内容 |
| created_at | datetime | 创建时间 |

- 按项目路径隔离，不同项目互不干扰
- 首次进入新项目时自动扫描项目结构，写入初始记忆
- 每次交互/审查后自动更新

---

## 4. 非功能需求

### 4.1 性能

| 指标 | 要求 |
|------|------|
| 单次对话响应 | < 10 秒（不含工具执行时间） |
| 文件读取 | < 1 秒 |
| 代码搜索 | < 5 秒（1000 文件规模） |
| 命令执行超时 | 30 秒（可配置） |
| 最大步数 | 15 步（可配置） |

### 4.2 可靠性

| 场景 | 处理方式 |
|------|----------|
| LLM API 超时 | 重试 2 次，间隔 2s/4s |
| 工具执行失败 | 把错误返回 LLM，让它决定重试或换方案 |
| 死循环 | step_count 硬限制 + 重复检测 + 总超时 |
| 文件不存在 | 提示用户，不自动创建（write_file 除外） |
| 命令执行超时 | 自动 kill 进程，返回超时错误 |

### 4.3 安全

| 风险 | 措施 |
|------|------|
| 误删文件 | write_file 覆盖前检查文件是否存在，存在则确认 |
| 危险命令 | run_command 维护黑名单（rm -rf /、format、mkfs 等） |
| 密钥泄露 | 禁止读取 .env、*.key、*.pem 等敏感文件 |
| 无限循环 | max_steps 硬限制，不可被 LLM 覆盖 |

---

## 5. 交互设计

### 5.1 CLI 交互

```
$ python main.py

🤖 代码助手已启动，输入你的需求（输入 quit 退出）

> 帮我看看 main.py 有没有问题

[Agent] 正在读取 main.py...
[Agent] 分析结果：
  1. 第 12 行：未使用的 import
  2. 第 25 行：缺少类型标注
  3. 第 38 行：异常处理过于宽泛，建议指定异常类型

需要我帮你修复吗？

> 帮我把第 12 行的没用的 import 删掉

[Agent] 正在编辑 main.py...
[Agent] 已删除第 12 行的 unused import: os

> 再帮我看看 utils/ 目录下有什么文件

[Agent] utils/ 目录内容：
  utils/__init__.py
  utils/helper.py
  utils/config.py

> quit
再见！
```

### 5.2 输出格式

| 类型 | 格式 |
|------|------|
| 思考过程 | [Agent] 前缀，灰色文字 |
| 工具调用 | [工具] 前缀，显示调用了什么工具 |
| 分析结果 | Markdown 格式，带编号 |
| 错误信息 | [错误] 前缀，红色文字 |
| 最终回答 | 正常文字，无前缀 |

---

## 6. 技术架构

### 6.1 技术栈

| 组件 | 选型 | 理由 |
|------|------|------|
| LLM | Claude API (Anthropic SDK) | function calling 好，200K 上下文 |
| 编排 | LangGraph | 有向图编排，状态管理清晰 |
| 缓存/会话 | Redis | 对话历史存储，后续扩展方便 |
| CLI 框架 | 纯 Python input() | 先简单，后面可换 rich/prompt_toolkit |
| GitHub 集成 | PyGithub / GitHub REST API | PR 评论、获取 diff |
| Git 钩子 | pre-push hook | push 前自动触发审查 |
| 长期记忆存储 | MySQL | 项目级记忆持久化，结构化查询 |
| 微信推送 | PushPlus | 审查结果推送到微信，免费 200 条/天 |
| 语言 | Python 3.10+ | LangGraph 原生支持 |

### 6.2 项目结构

```
aiagent/
├── config/
│   └── settings.py          # 配置（API key、模型、参数）
├── core/
│   ├── agent.py             # Agent 核心逻辑
│   ├── state.py             # LangGraph State 定义
│   ├── graph.py             # 图编排（节点、边、条件路由）
│   └── llm.py               # LLM 调用封装
├── tools/
│   ├── base.py              # 工具基类、注册机制
│   ├── file_tools.py        # read_file, write_file, edit_file
│   ├── shell_tools.py       # run_command
│   ├── search_tools.py      # search_code, list_files
│   ├── git_tools.py         # git_diff
│   ├── github_tools.py      # github_comment（PR 评论）
│   ├── push_tools.py        # push_wechat（PushPlus 微信推送）
│   └── safety.py            # 安全检查（命令黑名单、敏感文件）
├── memory/
│   ├── session.py           # Redis 短期记忆（对话历史）
│   ├── project_memory.py    # 项目级长期记忆（MySQL）
│   └── compressor.py        # 上下文压缩
├── reviewer/
│   ├── reviewer.py          # 代码审查核心逻辑
│   ├── rules.py             # 审查规则定义
│   ├── scorer.py            # 评分逻辑（按维度权重计算）
│   └── reporter.py          # 审查报告生成（GitHub PR 评论 / 本地文件 / 微信推送）
├── db/
│   └── schema.sql           # MySQL 建表语句
├── hooks/
│   └── pre-push             # Git pre-push hook 脚本
├── prompts/
│   ├── system.txt           # 交互模式系统提示词
│   └── reviewer.txt         # 审查模式系统提示词
├── main.py                  # 交互模式入口
├── review.py                # 审查模式入口（被 Git hook 调用）
└── requirements.txt         # 依赖
```

### 6.3 依赖

```
anthropic>=0.40.0
langgraph>=0.2.0
langchain-core>=0.3.0
redis>=5.0.0
PyGithub>=2.0.0
gitpython>=3.1.0
pymysql>=1.1.0
requests>=2.31.0
```

---

## 7. 里程碑

| 阶段 | 内容 | 交付物 | 预计时间 |
|------|------|--------|----------|
| M1 | LLM 对话 + 基础工具（read_file, run_command） | 能对话、能读文件、能跑命令 | 2~3 天 |
| M2 | 完整工具集 + 安全约束 | 8 个工具全部可用 | 2~3 天 |
| M3 | LangGraph 编排 + 多步任务 | 分析→修复→验证闭环 | 2~3 天 |
| M4 | Redis 记忆 + 多轮对话 + 上下文压缩 | 多轮对话、上下文指代 | 2~3 天 |
| M5 | 项目级长期记忆 | 每个项目独立记忆，自动学习项目特征 | 2~3 天 |
| M6 | GitHub 自动审查 | push 时自动审查，结果写入 PR 评论 | 3~4 天 |
| M7 | 优化 + 测试 + 稳定性 | 可日常使用 | 持续 |

---

## 8. 风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| LLM 幻觉导致错误修改 | 修改了不该改的代码 | edit_file 要求唯一匹配；修改前展示 diff 让用户确认 |
| 命令执行安全风险 | 误执行危险命令 | 命令黑名单 + 超时 + 用户确认 |
| Token 成本过高 | 长文件、多轮对话消耗大量 token | 上下文压缩 + 文件截断 + 摘要 |
| 死循环 | Agent 反复调用同一工具 | max_steps + 重复检测 + 总超时 |
| 工具调用格式错误 | LLM 输出的参数格式不对 | 参数校验 + 错误信息返回 LLM 重试 |

---

## 9. 开放问题

| 问题 | 选项 | 决策 |
|------|------|------|
| 是否需要用户确认再修改文件？ | A. 每次确认 B. 仅高风险确认 C. 直接修改 | B（write_file 覆盖和 run_command 确认） |
| CLI 交互用什么库？ | A. 纯 input() B. rich C. prompt_toolkit | A（先跑通，后面再美化） |
| 长期记忆要不要做？ | A. 本期做 B. 下期再做 | A（项目级长期记忆，P1） |
| 是否支持多项目？ | A. 单项目 B. 多项目切换 | B（按项目路径 hash 隔离记忆） |
| 审查结果发到哪里？ | A. 只写 PR 评论 B. 只写本地文件 C. 都写 | C（有 PR 写评论，没有写本地）+ 微信推送 |
| Git hook 用什么时机？ | A. pre-push B. post-push C. GitHub Actions | A（push 前审查，有问题可以拦住） |
| 微信用什么推送？ | A. PushPlus B. Server酱 C. 企业微信 | A（PushPlus，零门槛） |
