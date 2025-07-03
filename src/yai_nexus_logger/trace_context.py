from contextvars import ContextVar, Token
import logging
import uuid


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
        logging.debug(f"ContextVar set trace_id: {trace_id}")
        return self._trace_id_context.set(trace_id)

    def get_trace_id(self) -> str:
        """
        获取当前上下文的 trace_id。
        如果 trace_id 不存在，则会生成一个新的 UUID v4 并设置到上下文中。

        Returns:
            当前或新生成的 trace_id。
        """
        trace_id = self._trace_id_context.get()
        if trace_id is None:
            trace_id = str(uuid.uuid4())
            self.set_trace_id(trace_id)
        logging.debug(f"ContextVar get trace_id: {trace_id}")
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