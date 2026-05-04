"""统一日志 SDK 本地自检脚本。"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from tf_logging_sdk import bind_log_context, clear_log_context, setup_logging


def main() -> None:
    """执行基础能力自检。"""
    log_file_path = Path("logs/tf_logging_sdk_self_check.log")
    setup_logging(
        service_name="tf-logging-sdk-self-check",
        environment="dev",
        enable_file=True,
        log_file_path=str(log_file_path),
        enable_logstash=True,
        logstash_host=None,
        logstash_port=None,
    )

    logger = logging.getLogger(__name__)
    bind_log_context(
        trace_id="trace-self-check-001",
        task_id="task-self-check-001",
        topic="sdk.self.check",
        message_type="self.check",
        worker_type="unit",
    )
    logger.info(
        "开始执行 SDK 自检",
        extra={
            "duration_ms": 10,
            "request_data": {
                "password": "super-secret-password",
                "token": "token-value-1234567890",
                "email": "sdk-check@example.com",
            },
        },
    )
    clear_log_context()

    log_lines = log_file_path.read_text(encoding="utf-8").strip().splitlines()
    last_payload = json.loads(log_lines[-1])
    print(json.dumps(last_payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
