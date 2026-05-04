"""统一日志 SDK 最小接入示例。"""

from __future__ import annotations

import logging

from tf_logging_sdk import bind_log_context, clear_log_context, setup_logging


def main() -> None:
    """演示 SDK 的基本接入方式。"""
    setup_logging(
        service_name="example-service",
        environment="dev",
        enable_file=True,
        log_file_path="logs/example-service.log",
    )

    logger = logging.getLogger(__name__)
    bind_log_context(
        trace_id="trace-example-001",
        task_id="task-example-001",
        topic="example.topic",
        message_type="example.created",
    )
    logger.info(
        "示例任务开始处理",
        extra={
            "duration_ms": 20,
            "payload": {
                "password": "example-password",
                "email": "demo@example.com",
            },
        },
    )
    clear_log_context()


if __name__ == "__main__":
    main()
