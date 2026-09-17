"""工具注册机制：把 Python 函数注册为 LLM 可调用的工具。"""

# 全局工具注册表
_registry: dict[str, dict] = {}


def tool(name: str, description: str, parameters: dict):
    """装饰器：注册一个工具函数。"""
    def decorator(func):
        _registry[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "func": func,
        }
        return func
    return decorator


def get_tool_definitions() -> list[dict]:
    """获取所有工具的定义（传给 LLM）。"""
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "parameters": t["parameters"],
        }
        for t in _registry.values()
    ]


def execute_tool(name: str, args: dict) -> str:
    """执行一个工具，返回结果字符串。"""
    if name not in _registry:
        return f"错误：未知工具 '{name}'"

    func = _registry[name]["func"]
    try:
        result = func(**args)
        return str(result)
    except Exception as e:
        return f"工具执行出错：{type(e).__name__}: {e}"


def get_all_tool_names() -> list[str]:
    return list(_registry.keys())
