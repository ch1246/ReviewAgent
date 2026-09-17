"""Redis 短期记忆：对话历史存取。"""

import json
import redis
from config import settings


def get_redis() -> redis.Redis:
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD or None,
        decode_responses=True,
    )


def save_messages(session_id: str, messages: list[dict], ttl: int = 86400):
    """保存对话历史到 Redis。"""
    r = get_redis()
    key = f"chat:{session_id}:messages"
    r.set(key, json.dumps(messages, ensure_ascii=False), ex=ttl)


def load_messages(session_id: str) -> list[dict]:
    """从 Redis 加载对话历史。"""
    r = get_redis()
    key = f"chat:{session_id}:messages"
    data = r.get(key)
    if data:
        return json.loads(data)
    return []


def delete_session(session_id: str):
    """删除会话数据。"""
    r = get_redis()
    r.delete(f"chat:{session_id}:messages")
    r.delete(f"chat:{session_id}:last_file")
    r.delete(f"chat:{session_id}:last_command")


def save_last_file(session_id: str, file_path: str, ttl: int = 86400):
    """记录最近操作的文件（用于上下文指代）。"""
    r = get_redis()
    r.set(f"chat:{session_id}:last_file", file_path, ex=ttl)


def get_last_file(session_id: str) -> str:
    """获取最近操作的文件。"""
    r = get_redis()
    return r.get(f"chat:{session_id}:last_file") or ""


def save_last_command(session_id: str, command: str, ttl: int = 86400):
    """记录最近执行的命令。"""
    r = get_redis()
    r.set(f"chat:{session_id}:last_command", command, ex=ttl)


def get_last_command(session_id: str) -> str:
    """获取最近执行的命令。"""
    r = get_redis()
    return r.get(f"chat:{session_id}:last_command") or ""
