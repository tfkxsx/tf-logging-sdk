"""统一日志过滤与标准字段注入。"""

from __future__ import annotations

import logging
import traceback
from datetime import datetime, timezone
from typing import Any

from tf_logging_sdk.config import (
    DEFAULT_EXTRA_FIELDS,
    DEFAULT_STANDARD_FIELDS,
    LoggingConfig,
    RESERVED_LOG_RECORD_FIELDS,
)
from tf_logging_sdk.context import get_log_context
from tf_logging_sdk.masking import LogMasker


class ContextEnrichmentFilter(logging.Filter):
    """为日志记录注入标准字段和上下文。"""

    def __init__(self, config: LoggingConfig, masker: LogMasker):
        """初始化过滤器。

        参数:
            config: 日志初始化配置。
            masker: 脱敏器。
        """
        super().__init__()
        self._config = config
        self._masker = masker

    def filter(self, record: logging.LogRecord) -> bool:
        """将标准字段写回日志记录，供 formatter 和 handler 使用。"""
        context = get_log_context()
        message = record.getMessage()
        masked_message = self._masker.mask_text(str(message))
        record.msg = masked_message
        record.args = ()

        extra_payload = self._collect_extra_payload(record)
        masked_extra_payload = self._masker.mask(extra_payload)

        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        standard_payload: dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "service": self._config.service_name,
            "environment": self._config.environment,
            "module": record.name,
            "message": masked_message,
            "trace_id": context.get("trace_id"),
            "task_id": context.get("task_id"),
            "space_id": context.get("space_id"),
            "message_type": context.get("message_type"),
            "topic": context.get("topic"),
            "consumer_group": context.get("consumer_group"),
            "worker_type": context.get("worker_type"),
            "region": context.get("region"),
            "duration_ms": masked_extra_payload.get("duration_ms"),
            "error_code": masked_extra_payload.get("error_code"),
            "error": self._build_error_field(record, masked_extra_payload),
        }

        for field_name, field_value in context.items():
            standard_payload.setdefault(field_name, field_value)
        for field_name, field_value in masked_extra_payload.items():
            standard_payload.setdefault(field_name, field_value)

        standard_payload["standard_fields"] = list(DEFAULT_STANDARD_FIELDS)

        for field_name, field_value in standard_payload.items():
            setattr(record, field_name, field_value)
        record.structured_payload = {
            field_name: getattr(record, field_name, None)
            for field_name in self._config.standard_fields
        }
        record.structured_payload["extra"] = {
            field_name: field_value
            for field_name, field_value in standard_payload.items()
            if field_name not in self._config.standard_fields
            and field_name != "standard_fields"
        }
        return True

    def _collect_extra_payload(self, record: logging.LogRecord) -> dict[str, Any]:
        """提取调用方通过 extra 注入的字段。"""
        extra_payload: dict[str, Any] = {}
        for field_name, field_value in record.__dict__.items():
            if field_name in RESERVED_LOG_RECORD_FIELDS:
                continue
            if field_name in DEFAULT_STANDARD_FIELDS and field_name not in DEFAULT_EXTRA_FIELDS:
                continue
            if field_name == "structured_payload":
                continue
            extra_payload[field_name] = field_value

        for field_name in DEFAULT_EXTRA_FIELDS:
            extra_payload.setdefault(field_name, None)
        return extra_payload

    def _build_error_field(
        self,
        record: logging.LogRecord,
        masked_extra_payload: dict[str, Any],
    ) -> str | None:
        """统一构建错误字段。"""
        if masked_extra_payload.get("error"):
            return str(masked_extra_payload["error"])
        if not record.exc_info:
            return None
        formatted_exception = "".join(traceback.format_exception(*record.exc_info)).strip()
        return self._masker.mask_text(formatted_exception)
