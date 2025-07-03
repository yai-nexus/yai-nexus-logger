"""Integration tests for the logger."""
from yai_nexus_logger.logger_builder import LoggerBuilder
from yai_nexus_logger.trace_context import trace_context

def test_logger_integration_with_console_and_file(tmp_path, capsys):
    """
    Integration test to ensure the logger works end-to-end with console and file handlers.
    """
    log_file_path = tmp_path / "test_app.log"

    # 1. Build the logger
    builder = LoggerBuilder("integration_test", level="DEBUG")
    logger = builder.with_console_handler() \
                    .with_file_handler(path=str(log_file_path)) \
                    .build()

    # 2. Set a trace_id
    trace_id = "test-trace-id-123"
    token = trace_context.set_trace_id(trace_id)

    # 3. Log messages
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")

    # 4. Check console output
    captured = capsys.readouterr()
    stdout = captured.out.strip()
    
    # Verify console output
    assert "INFO" in stdout
    assert "test_logger_integration" in stdout
    assert "This is an info message." in stdout
    assert trace_id in stdout
    assert "WARNING" in stdout
    assert "This is a warning message." in stdout

    # 5. Check file output
    assert log_file_path.exists()
    with open(log_file_path, 'r', encoding="utf-8") as f:
        file_content = f.read().strip()

    # Verify file content
    assert "INFO" in file_content
    assert "test_logger_integration" in file_content
    assert "This is an info message." in file_content
    assert trace_id in file_content
    assert "WARNING" in file_content
    assert "This is a warning message." in file_content

    # Clean up context
    trace_context.reset_trace_id(token) 