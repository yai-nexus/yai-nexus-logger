# tests/yai_nexus_logger/unit/test_trace_context.py

import uuid

import pytest

from yai_nexus_logger import trace_context


# 这个 fixture 会在每个测试函数运行前自动执行
@pytest.fixture(autouse=True)
def cleanup_trace_context():
    """在每次测试前清理 trace_context，确保测试隔离"""
    trace_context.clear()
    yield
    trace_context.clear()


def test_get_trace_id_returns_none_when_empty():
    """
    测试当上下文中没有 trace_id 时，get_trace_id() 返回 None。
    """
    # 在干净的上下文中，第一次调用应返回 None
    trace_id = trace_context.get_trace_id()
    assert trace_id is None


def test_get_or_create_trace_id_generates_uuid():
    """
    测试当上下文中没有 trace_id 时，get_or_create_trace_id() 是否会生成一个有效的 UUID。
    """
    # 在干净的上下文中，第一次调用应生成一个新的 ID
    trace_id = trace_context.get_or_create_trace_id()
    assert isinstance(trace_id, str)
    try:
        # 验证其是否为有效的 UUID v4
        uuid.UUID(trace_id, version=4)
    except ValueError:
        assert False, f"{trace_id} is not a valid UUID v4"


def test_set_and_get_trace_id():
    """
    测试 set_trace_id 和 get_trace_id 是否能正确设置和获取 ID。
    """
    custom_id = "my-custom-test-id"
    token = trace_context.set_trace_id(custom_id)
    assert trace_context.get_trace_id() == custom_id
    # 清理
    trace_context.reset_trace_id(token)


def test_reset_trace_id():
    """
    测试 reset_trace_id 是否能正确重置上下文。
    """
    custom_id = "my-test-id-to-reset"
    token = trace_context.set_trace_id(custom_id)
    # 验证ID已设置
    assert trace_context.get_trace_id() == custom_id

    # 重置
    trace_context.reset_trace_id(token)

    # 重置后，获取到的ID应该是 None，因为我们回到了空上下文
    new_id = trace_context.get_trace_id()
    assert new_id is None


def test_multiple_trace_ids_stacking():
    """
    测试 trace_id 的堆栈功能是否正常。
    """
    id1 = "first-level-id"
    id2 = "second-level-id"

    token1 = trace_context.set_trace_id(id1)
    assert trace_context.get_trace_id() == id1

    token2 = trace_context.set_trace_id(id2)
    assert trace_context.get_trace_id() == id2

    # 重置第二个ID，应该恢复到第一个
    trace_context.reset_trace_id(token2)
    assert trace_context.get_trace_id() == id1

    # 重置第一个ID，应该恢复到初始状态（None）
    trace_context.reset_trace_id(token1)
    new_id = trace_context.get_trace_id()
    assert new_id is None


def test_clear_context():
    """
    测试 clear() 是否能清除所有 trace_id。
    """
    trace_context.set_trace_id("id-to-be-cleared-1")
    trace_context.set_trace_id("id-to-be-cleared-2")

    # 确认最顶层的ID是我们刚设置的
    assert trace_context.get_trace_id() == "id-to-be-cleared-2"

    trace_context.clear()

    # 清除后，获取ID应该返回 None
    new_id = trace_context.get_trace_id()
    assert new_id is None
