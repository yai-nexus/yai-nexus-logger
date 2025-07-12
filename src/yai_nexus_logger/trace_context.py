# src/yai_nexus_logger/trace_context.py

import uuid
from contextvars import ContextVar, Token
from typing import Optional

# 使用 ContextVar 来存储 trace_id，确保在异步代码中上下文安全
# The context variable for storing the trace ID.
# 使用 None 作为默认值，表示当前上下文中没有设置 trace_id。
_trace_id_context: ContextVar[Optional[str]] = ContextVar("trace_id_context", default=None)


class TraceContext:
    """
    一个用于管理追踪ID（trace_id）的上下文管理器。
    支持在同步和异步代码中安全地设置、获取和重置 trace_id。
    使用 `ContextVar[str]` 来简化实现，避免了手动管理堆栈。
    """

    def get_trace_id(self) -> Optional[str]:
        """
        获取当前的 trace_id。
        如果上下文中没有 trace_id，返回 None。
        """
        return _trace_id_context.get()

    def get_or_create_trace_id(self) -> str:
        """
        获取当前的 trace_id。
        如果上下文中没有 trace_id，会自动生成一个新的 UUIDv4 并设置为当前 trace_id。
        """
        trace_id = _trace_id_context.get()
        if trace_id is None:
            # 如果没有 trace_id, 生成一个新的并设置
            new_id = str(uuid.uuid4())
            _trace_id_context.set(new_id)
            return new_id
        return trace_id

    def set_trace_id(self, trace_id: str) -> Token:
        """
        设置一个新的 trace_id 到上下文中。

        Args:
            trace_id (str): 要设置的追踪ID。

        Returns:
            Token: 一个令牌，可以用于之后调用 reset_trace_id 来恢复上下文。
        """
        return _trace_id_context.set(trace_id)

    def reset_trace_id(self, token: Token):
        """
        使用 set_trace_id 返回的令牌来重置上下文。

        Args:
            token (Token): 从 set_trace_id 调用中获取的令牌。
        """
        _trace_id_context.reset(token)

    def clear(self):
        """
        完全清空当前的 trace_id 上下文。
        这在测试环境中尤其有用，可以确保不同测试用例之间的隔离。
        """
        _trace_id_context.set(None)


# 创建一个单例，供整个应用使用
trace_context = TraceContext()
