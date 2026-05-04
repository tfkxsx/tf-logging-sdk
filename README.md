# tf-logging-sdk

项目级统一日志 SDK，提供统一初始化入口、标准字段、上下文注入、敏感信息脱敏，以及 `stdout / file / Logstash TCP` 多通道输出能力。

仓库地址：

- GitHub: [https://github.com/tfkxsx/tf-logging-sdk](https://github.com/tfkxsx/tf-logging-sdk)
- Git: `git@github.com:tfkxsx/tf-logging-sdk.git`

## 功能特性

1. 提供统一入口 `setup_logging`
2. 提供 `bind_log_context` 和 `clear_log_context`
3. 统一输出标准字段，便于检索和排障
4. 默认脱敏 `password`、`token`、`authorization`、`cookie`、`secret` 等敏感字段
5. 支持控制台可读输出
6. 支持 JSON 文件滚动日志
7. 支持 TCP Logstash 结构化输出
8. 未配置 Logstash 时自动降级，不影响本地启动

## 安装

```bash
pip install tf-logging-sdk
```

本地开发安装：

```bash
pip install -e .[dev]
```

## 快速开始

```python
import logging

from tf_logging_sdk import bind_log_context, clear_log_context, setup_logging

setup_logging(
    service_name="kafka-task",
    environment="dev",
    enable_file=True,
    log_file_path="logs/kafka-task.log",
    enable_logstash=False,
)

logger = logging.getLogger(__name__)

bind_log_context(
    trace_id="trace-demo-001",
    task_id="task-demo-001",
    space_id="space-demo-001",
    topic="task.dispatch",
    message_type="task.created",
)

logger.info(
    "开始处理任务",
    extra={
        "duration_ms": 12,
        "request_payload": {
            "token": "abcd1234567890",
            "email": "demo@example.com",
        },
    },
)

clear_log_context()
```

## 标准字段

SDK 默认统一输出以下字段：

1. `timestamp`
2. `level`
3. `service`
4. `environment`
5. `module`
6. `message`
7. `trace_id`
8. `task_id`
9. `space_id`
10. `message_type`
11. `topic`
12. `consumer_group`
13. `worker_type`
14. `region`
15. `duration_ms`
16. `error_code`
17. `error`

## 输出方式

### 1. 控制台输出

```python
setup_logging(
    service_name="schedule-task",
    environment="dev",
)
```

### 2. 文件日志

```python
setup_logging(
    service_name="extractors",
    environment="dev",
    enable_file=True,
    log_file_path="logs/extractors.log",
    file_max_bytes=50 * 1024 * 1024,
    file_backup_count=5,
)
```

### 3. Logstash 输出

```python
setup_logging(
    service_name="tf-data",
    environment="prod",
    enable_logstash=True,
    logstash_host="127.0.0.1",
    logstash_port=5959,
)
```

## 上下文注入

```python
from tf_logging_sdk import bind_log_context, clear_log_context

bind_log_context(
    trace_id="trace-001",
    task_id="task-001",
    topic="task.dispatch",
    message_type="task.created",
    consumer_group="group-task",
    worker_type="consumer",
)

clear_log_context()
```

SDK 基于 `contextvars` 管理上下文，避免不同线程或异步任务串线。

## 脱敏说明

默认脱敏字段：

1. `password`
2. `token`
3. `authorization`
4. `cookie`
5. `secret`
6. `access_key`
7. `proxy_password`
8. `phone`
9. `email`

扩展示例：

```python
setup_logging(
    service_name="demo-service",
    environment="test",
    extra_mask_fields=["session_id", "private_key"],
)
```

## 项目结构

```text
tf_logging_sdk/
├── examples/
├── src/
│   └── tf_logging_sdk/
├── LICENSE
├── MANIFEST.in
├── README.md
├── pyproject.toml
├── 统一日志SDK设计说明.md
├── 统一日志SDK接入指南.md
└── 统一日志SDK验收记录.md
```

## 文档

1. [统一日志SDK设计说明.md](./统一日志SDK设计说明.md)
2. [统一日志SDK接入指南.md](./统一日志SDK接入指南.md)
3. [统一日志SDK验收记录.md](./统一日志SDK验收记录.md)

## 本地验证

```bash
python -m compileall src/tf_logging_sdk
python -m tf_logging_sdk.examples.self_check
```

说明：

1. `self_check.py` 用于验证标准字段、上下文注入、文件输出与脱敏结果
2. 若按 `src` 布局直接执行模块，建议先执行 `pip install -e .`
