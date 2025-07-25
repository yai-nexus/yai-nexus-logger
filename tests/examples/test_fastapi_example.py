"""Tests for the FastAPI example application."""

from fastapi.testclient import TestClient

from examples.fastapi_example import create_app

# 使用 TestClient 来测试我们的 FastAPI 应用
# 通过调用 create_app() 来获取 app 实例
client = TestClient(create_app())


def test_root_endpoint():
    """
    测试根路径是否能正常返回，并检查响应头中是否有 X-Trace-ID。
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

    # 验证中间件是否添加了 trace_id 头
    assert "X-Trace-ID" in response.headers
    assert len(response.headers["X-Trace-ID"]) > 0


def test_middleware_uses_existing_trace_id():
    """
    测试当请求头中提供了 X-Trace-ID 时，中间件是否会使用它。
    """
    custom_trace_id = "my-awesome-custom-trace-id"
    headers = {"X-Trace-ID": custom_trace_id}

    response = client.get("/", headers=headers)

    assert response.status_code == 200
    assert response.headers["X-Trace-ID"] == custom_trace_id


def test_error_endpoint_logging():
    """
    测试错误路径是否按预期工作。
    我们无法在这里直接检查日志输出，但可以验证端点是否正常响应，
    以及 trace_id 是否仍在响应头中。
    """
    response = client.get("/error")
    assert response.status_code == 200
    assert response.json() == {"message": "An error was logged."}
    assert "X-Trace-ID" in response.headers
