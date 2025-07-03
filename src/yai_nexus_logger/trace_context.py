# src/yai_nexus_logger/trace_context.py

import uuid
from contextvars import ContextVar, Token
from typing import List, Optional

# 使用 ContextVar 来存储 trace_id 堆栈，确保在异步代码中上下文安全
# The context variable for storing the trace ID stack.
_trace_id_context: ContextVar[List[str]] = ContextVar("trace_id_context", default=[])


class TraceContext:
    """
    一个用于管理追踪ID（trace_id）的上下文管理器。
    支持在同步和异步代码中安全地设置、获取和重置 trace_id。
    """

    def get_trace_id(self) -> str:
        """
        获取当前的 trace_id。
        如果上下文中没有 trace_id，会自动生成一个新的 UUIDv4 并返回。
        """
        stack = _trace_id_context.get()
        if not stack:
            # 如果堆栈为空，生成一个新的 trace_id 并放入堆栈
            new_id = str(uuid.uuid4())
            stack.append(new_id)
            _trace_id_context.set(stack)
            return new_id
        return stack[-1]

    def set_trace_id(self, trace_id: str) -> Token:
        """
        设置一个新的 trace_id 到上下文堆栈中。

        Args:
            trace_id (str): 要设置的追踪ID。

        Returns:
            Token: 一个令牌，可以用于之后调用 reset_trace_id 来恢复上下文。
        """
        stack = _trace_id_context.get().copy()
        stack.append(trace_id)
        return _trace_id_context.set(stack)

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
        _trace_id_context.set([])


# 创建一个单例，供整个应用使用
trace_context = TraceContext()
