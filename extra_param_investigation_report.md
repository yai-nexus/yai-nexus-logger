# yai-nexus-logger `extra` 参数支持情况调研报告

## 1. 结论

**核心结论：** 目前 `yai-nexus-logger` **不完全支持** Python `logging` 模块的 `extra` 参数。

尽管项目的 `README.md` 和示例代码中展示了 `extra` 的用法，但其核心实现（格式化器和处理器）会**静默忽略** `extra` 中传递的自定义数据，导致这些数据不会出现在最终的控制台、文件或 SLS 日志输出中。

---

## 2. 调研背景

用户希望了解 `yai-nexus-logger` 是否支持通过 `extra` 参数向日志中添加自定义字段，例如：

```python
logger.info("用户登录", extra={"user_id": "123", "ip_address": "192.168.1.1"})
```

---

## 3. 分析过程

### 3.1. 表面现象：文档与实现存在矛盾

- **文档/示例表现**：
  - `README.md` 和 `examples/basic_example.py` 中均存在使用 `extra` 参数的示例代码，暗示该功能受支持。
- **初步代码审查**：
  - 通过对项目 `tests/` 目录进行搜索，**未发现**任何针对 `extra` 参数功能的自动化测试用例，这通常是功能缺失的一个危险信号。

### 3.2. 深入代码实现

#### a. 格式化器 (`Formatter`) 分析

日志的最终输出由 `Formatter` 决定。通过分析 `src/yai_nexus_logger/configurator.py`，我们发现：

1.  **唯一的格式化器**：项目默认且唯一使用的格式化器是 `src/yai_nexus_logger/internal/internal_formatter.py` 中定义的 `InternalFormatter`。

2.  **固定的格式字符串**：`configurator.py` 中定义了全局的日志格式 `LOGGING_FORMAT`：
    ```python
    LOGGING_FORMAT = (
        "%(asctime)s.%(msecs)03d | %(levelname)-7s | "
        "%(module)s:%(lineno)d | [%(trace_id)s] | %(message)s"
    )
    ```

**关键点**：Python 的 `logging.Formatter` 只会处理和渲染格式字符串中明确存在的属性（如 `%(levelname)s`）。由于 `LOGGING_FORMAT` 中不包含任何用于渲染 `extra` 字典中自定义键的占位符（例如 `%(user_id)s`），因此即使 `extra` 数据被附加到 `LogRecord` 对象上，`InternalFormatter` 在格式化时也会完全忽略它。

#### b. SLS 处理器 (`SLSLogHandler`) 分析

对于 SLS 日志，`src/yai_nexus_logger/internal/internal_sls_handler.py` 中的 `emit` 方法负责构建发送到阿里云的日志内容。其实现如下：

```python
# 截取自 internal_sls_handler.py
contents = [
    ("message", record.getMessage()),
    ("level", record.levelname),
    ("logger", record.name),
    # ... 其他硬编码的字段
    ("trace_id", current_trace_id),
]
```

**关键点**：`SLSLogHandler` 从 `LogRecord` 对象中提取一个**硬编码的字段列表**来构建日志内容。它没有包含任何逻辑来检查 `record.__dict__` 中是否存在非标准属性（即来自 `extra` 的属性），因此 `extra` 数据同样被忽略。

---

## 4. 总结与建议

### 总结

`yai-nexus-logger` 目前存在**文档与实现不一致**的问题。虽然文档和示例鼓励用户使用 `extra` 参数，但日志系统的核心组件（`InternalFormatter` 和 `SLSLogHandler`）并未实现对 `extra` 参数的通用处理逻辑，导致其被静默丢弃。

### 建议

根据项目需求，可以考虑以下两种方案：

1.  **修正文档（短期方案）**：
    - 从 `README.md` 和 `examples` 中移除关于 `extra` 参数的用法说明，避免误导用户。

2.  **实现 `extra` 支持（长期方案）**：
    - **对于文本日志**：考虑引入一个新的 `JSONFormatter`。JSON 格式天然适合动态添加键值对，可以迭代 `LogRecord` 的 `__dict__` 属性，将所有非标准字段自动添加到 JSON 输出中。
    - **对于 SLS 日志**：修改 `SLSLogHandler` 的 `emit` 方法，使其能够动态地将 `extra` 中的内容添加到 `contents` 列表中。

这样做可以大大增强日志系统的灵活性和实用性，使其与 Python `logging` 模块的集成更加完整。 