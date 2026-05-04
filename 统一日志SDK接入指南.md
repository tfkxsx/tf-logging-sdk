# 统一日志SDK接入指南

## 1. 接入目标

本文档用于指导 `tf-data`、`kafka-task`、`kafkaTask2`、`extractors`、`AutoParse`、`scheduleTask` 接入统一日志 SDK。

## 2. 初始化方式

```python
from tf_logging_sdk import setup_logging

setup_logging(
    service_name="kafka-task",
    environment="dev",
    logstash_host="127.0.0.1",
    logstash_port=5959,
    enable_file=True,
    log_file_path="logs/kafka-task.log",
    file_max_bytes=50 * 1024 * 1024,
    file_backup_count=5,
)
```

## 3. 最小接入步骤

1. 在服务启动入口调用 `setup_logging`
2. 业务代码继续使用 `logging.getLogger(__name__)`
3. 在任务开始时调用 `bind_log_context`
4. 在任务结束时调用 `clear_log_context`

## 4. 上下文注入示例

```python
import logging

from tf_logging_sdk import bind_log_context, clear_log_context

logger = logging.getLogger(__name__)

bind_log_context(
    trace_id=trace_id,
    task_id=task_id,
    space_id=space_id,
    message_type=message_type,
    topic=topic,
    consumer_group=consumer_group,
)

logger.info("开始消费任务", extra={"duration_ms": 15})

clear_log_context()
```

## 5. 文件日志示例

```python
setup_logging(
    service_name="extractors",
    environment="dev",
    enable_file=True,
    log_file_path="logs/extractors.log",
)
```

## 6. Logstash 接入示例

```python
setup_logging(
    service_name="tf-data",
    environment="prod",
    enable_logstash=True,
    logstash_host="logstash.internal",
    logstash_port=5959,
)
```

## 7. 脱敏扩展示例

```python
setup_logging(
    service_name="scheduleTask",
    environment="test",
    extra_mask_fields=["session_id", "private_key"],
)
```

## 8. 推荐接入点

1. `tf-data`
   推荐在 `app.py` 和独立脚本入口统一初始化。
2. `kafka-task`
   推荐在 `app/__init__.py` 或消费入口统一初始化。
3. `kafkaTask2`
   推荐在 `app/__init__.py` 或消费入口统一初始化。
4. `extractors`
   推荐在 `start_consumer.py` 初始化，替换当前 `basicConfig`。
5. `AutoParse`
   推荐在 API 启动入口统一初始化。
6. `scheduleTask`
   推荐在 `start_scheduler.py` 初始化，替换当前 `basicConfig`。

## 9. 注意事项

1. 日志说明保持中文，异常信息保持英文
2. 结构化数据优先通过 `extra` 传递，便于字段检索与脱敏
3. 任务结束后务必清理上下文，避免任务间字段串线
