"""Manages the trace context using contextvars for request tracing."""

import logging
import uuid
from contextvars import ContextVar, Token


class TraceContext:
    """
    一个用于管理 trace_id 上下文的类。
    它封装了 ContextVar，并提供了用于设置、获取和重置 trace_id 的方法。
    """

    def __init__(self):
        self._trace_id_context: ContextVar[str | None] = ContextVar(
            "trace_id", default=None
        )

    def set_trace_id(self, trace_id: str) -> Token:
        """
        设置当前请求的 trace_id 到 ContextVar 中。

        Args:
            trace_id: 要设置的 trace_id。

        Returns:
            一个 token 对象，可用于重置 context var。
        """
        logging.debug("ContextVar set trace_id: %s", trace_id)
        return self._trace_id_context.set(trace_id)

    def get_trace_id(self, create_if_missing: bool = True) -> str | None:
        """
        获取当前上下文的 trace_id。
        如果 trace_id 不存在，则会根据 `create_if_missing` 的值决定是否创建。

        Args:
            create_if_missing (bool): 如果为 True 且 trace_id 不存在，则创建新的。

        Returns:
            当前或新生成的 trace_id，或者 None。
        """
        trace_id = self._trace_id_context.get()
        if trace_id is None and create_if_missing:
            trace_id = str(uuid.uuid4())
            self.set_trace_id(trace_id)
        logging.debug("ContextVar get trace_id: %s", trace_id)
        return trace_id

    def reset_trace_id(self, token: Token) -> None:
        """
        使用 token 重置 trace_id。

        Args:
            token: set_trace_id 返回的 token。
        """
        self._trace_id_context.reset(token)


# 创建一个 TraceContext 的单例，供整个应用使用
trace_context = TraceContext()
