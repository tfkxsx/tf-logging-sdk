# 统一日志SDK设计说明

## 1. 文档目标

本文档说明第一阶段 `统一日志 SDK` 的设计方案、模块职责、关键能力与边界。

## 2. 目录结构

```text
tf_logging_sdk/
  __init__.py
  config.py
  context.py
  formatter.py
  filters.py
  handlers.py
  masking.py
  README.md
  examples/
```

## 3. 设计目标

1. 提供统一初始化入口 `setup_logging`
2. 不依赖 `tf-data` 或任一业务服务的私有配置
3. 支持 `stdout`、文件日志、Logstash TCP 输出
4. 支持上下文注入，避免任务排障时缺少关键字段
5. 支持敏感字段默认脱敏，并允许扩展

## 4. 模块职责

1. `config.py`
   定义 `LoggingConfig`、标准字段、默认脱敏字段与保留字段集合。
2. `context.py`
   基于 `contextvars` 管理当前任务上下文，保证线程和异步场景不串线。
3. `masking.py`
   递归脱敏字典、列表、元组等结构，并对常见文本片段做轻量脱敏。
4. `filters.py`
   将标准字段、上下文和异常信息写入 `LogRecord`，同时完成脱敏。
5. `formatter.py`
   提供控制台可读格式和文件 / Logstash 的 JSON 结构化格式。
6. `handlers.py`
   提供 `setup_logging`，按配置构建 `stdout`、滚动文件、TCP Logstash handler。

## 5. 标准字段

SDK 统一输出以下字段：

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

## 6. 上下文模型

SDK 默认支持以下上下文字段注入：

1. `trace_id`
2. `task_id`
3. `space_id`
4. `message_type`
5. `topic`
6. `consumer_group`
7. `worker_type`
8. `region`

绑定方式：

```python
from tf_logging_sdk import bind_log_context, clear_log_context

bind_log_context(
    trace_id="trace-001",
    task_id="task-001",
    topic="task.dispatch",
    message_type="task.created",
)
```

## 7. 输出策略

1. 默认输出到 `stdout`
2. 配置 `enable_file=True` 时输出滚动文件日志
3. 配置了 `enable_logstash=True` 且同时提供 `logstash_host`、`logstash_port` 时输出到 Logstash
4. 未配置 Logstash 时自动降级，不阻塞服务启动
5. 网络日志发送失败时静默降级，不中断业务流程

## 8. 脱敏策略

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

脱敏规则：

1. 命中字段名时优先按字段脱敏
2. 对文本消息中的 `key=value`、`key:` 等常见片段做轻量脱敏
3. 结构化对象递归处理，避免嵌套字段漏脱敏

## 9. 已知边界

1. 当前 Logstash 输出采用通用 TCP JSON 协议，便于脱离第三方包独立运行
2. 对自由文本的脱敏属于兜底能力，推荐业务日志优先通过 `extra` 传结构化字段
3. SDK 负责统一初始化和输出，不主动改造各业务模块现有 `logging.getLogger` 调用方式
