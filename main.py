import sys
import uuid
import logging
import hashlib
from pathlib import Path
from config import settings

# 导入所有工具（触发注册）
import tools.file_tools
import tools.shell_tools
import tools.search_tools
import tools.git_tools
import tools.github_tools
import tools.push_tools

from core.graph import run_agent
from memory.session import save_messages, load_messages
from memory.compressor import compress_messages
import redis as redis_lib

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("agent.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def load_system_prompt() -> str:
    prompt_file = Path(__file__).parent / "prompts" / "system.txt"
    return prompt_file.read_text(encoding="utf-8")


def check_config():
    missing = []
    if not settings.LLM_API_KEY:
        missing.append("LLM_API_KEY")
    if missing:
        print(f"错误：请在 .env 文件中配置：{', '.join(missing)}")
        sys.exit(1)


def _get_project_key() -> str:
    """根据当前工作目录生成项目唯一标识。"""
    cwd = str(Path.cwd())
    return hashlib.md5(cwd.encode()).hexdigest()[:12]


def _get_or_create_session(project_key: str) -> tuple[str, bool]:
    """获取项目的会话 ID，不存在则创建。返回 (session_id, is_existing)。"""
    try:
        r = redis_lib.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD or None,
            decode_responses=True,
        )
        key = f"project:{project_key}:session"
        session_id = r.get(key)
        if session_id:
            return session_id, True

        # 创建新会话
        session_id = str(uuid.uuid4())[:8]
        r.set(key, session_id, ex=86400 * 7)  # 7 天过期
        return session_id, False
    except Exception:
        # Redis 不可用，用内存会话
        return str(uuid.uuid4())[:8], False


def main():
    check_config()

    system_prompt = load_system_prompt()
    project_key = _get_project_key()
    cwd = str(Path.cwd())

    print("=" * 50)
    print("  代码助手 Agent")
    print("=" * 50)
    print(f"\n项目目录：{cwd}")

    # 自动恢复会话
    session_id, is_existing = _get_or_create_session(project_key)

    if is_existing:
        messages = load_messages(session_id)
        if messages:
            print(f"已恢复上次对话（{len(messages)} 条消息）")
            print("输入 new 开始新对话，或直接继续\n")
        else:
            is_existing = False

    if not is_existing:
        messages = []
        print("新对话已创建\n")

    print(f"会话 ID：{session_id}")
    print("命令：quit=退出 | new=新对话 | review=代码审查\n")

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            save_messages(session_id, messages)
            print("对话已保存。再见！")
            break

        # 新对话
        if user_input.lower() == "new":
            session_id = str(uuid.uuid4())[:8]
            messages = []
            # 更新项目绑定
            try:
                r = redis_lib.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD or None,
                    decode_responses=True,
                )
                r.set(f"project:{project_key}:session", session_id, ex=86400 * 7)
            except Exception:
                pass
            print(f"新对话已创建（会话 {session_id}）\n")
            continue

        # 快捷命令：运行审查
        if user_input.lower() == "review":
            _run_review_shortcut()
            continue

        # 压缩上下文
        messages = compress_messages(messages)

        logger.info(f"用户输入：{user_input[:100]}")

        try:
            answer, messages = run_agent(
                user_input=user_input,
                messages=messages,
                system_prompt=system_prompt,
                session_id=session_id,
            )

            if answer:
                print(f"\n{answer}\n")

            save_messages(session_id, messages)
            logger.info(f"回复完成，消息数：{len(messages)}")

        except Exception as e:
            logger.error(f"运行出错：{e}", exc_info=True)
            print(f"出错：{e}\n")


def _run_review_shortcut():
    import subprocess
    review_script = Path(__file__).parent / "review.py"
    try:
        subprocess.run([sys.executable, str(review_script)], check=False)
    except Exception as e:
        print(f"运行审查出错：{e}")


if __name__ == "__main__":
    main()
