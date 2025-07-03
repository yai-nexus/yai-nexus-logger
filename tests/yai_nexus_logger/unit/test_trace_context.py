import uuid

from yai_nexus_logger.trace_context import TraceContext


def test_get_trace_id_generates_uuid():
    """
    测试当上下文中没有 trace_id 时，get_trace_id() 是否会生成一个有效的 UUID。
    """
    trace_context = TraceContext()
    # 在干净的上下文中，第一次调用应生成一个新的 ID
    trace_id = trace_context.get_trace_id()
    assert isinstance(trace_id, str)
    try:
        # 验证其是否为有效的 UUID v4
        uuid.UUID(trace_id, version=4)
    except ValueError:
        assert False, f"{trace_id} is not a valid UUID v4"


def test_set_and_get_trace_id():
    """
    测试能否成功设置并获取 trace_id。
    """
    trace_context = TraceContext()
    custom_id = "my-test-id-123"
    token = trace_context.set_trace_id(custom_id)
    
    retrieved_id = trace_context.get_trace_id()
    assert retrieved_id == custom_id
    
    # 清理上下文
    trace_context.reset_trace_id(token)


def test_reset_trace_id():
    """
    测试 reset_trace_id 是否能正确重置上下文。
    """
    trace_context = TraceContext()
    custom_id = "my-test-id-to-reset"
    token = trace_context.set_trace_id(custom_id)
    
    # 验证ID已设置
    assert trace_context.get_trace_id() == custom_id
    
    # 重置
    trace_context.reset_trace_id(token)
    
    # 重置后，获取到的ID应该是一个新生成的ID，而不是我们之前设置的
    new_id = trace_context.get_trace_id()
    assert new_id != custom_id
    try:
        uuid.UUID(new_id, version=4)
    except ValueError:
        assert False, f"After reset, expected a new UUID, but got {new_id}" 