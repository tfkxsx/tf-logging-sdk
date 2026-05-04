"""统一日志格式化器。"""

from __future__ import annotations

import json
import logging
from typing import Any


class ConsoleFormatter(logging.Formatter):
    """控制台可读格式化器。"""

    def format(self, record: logging.LogRecord) -> str:
        """输出便于人工排查的单行文本。"""
        payload = getattr(record, "structured_payload", {})
        parts = [
            str(payload.get("timestamp", "")),
            f"[{payload.get('level', '')}]",
            f"[{payload.get('service', '')}]",
            f"[{payload.get('environment', '')}]",
            f"[{payload.get('module', '')}]",
            str(payload.get("message", "")),
        ]

        optional_fields = [
            "trace_id",
            "task_id",
            "space_id",
            "message_type",
            "topic",
            "consumer_group",
            "worker_type",
            "region",
            "duration_ms",
            "error_code",
        ]
        for field_name in optional_fields:
            field_value = payload.get(field_name)
            if field_value is not None and field_value != "":
                parts.append(f"{field_name}={field_value}")

        error_value = payload.get("error")
        if error_value:
            parts.append(f"error={error_value}")
        return " ".join(parts)


class JsonFormatter(logging.Formatter):
    """结构化 JSON 格式化器。"""

    def format(self, record: logging.LogRecord) -> str:
        """输出 JSON 文本，供文件和网络日志消费。"""
        payload = dict(getattr(record, "structured_payload", {}))
        return json.dumps(self._normalize_payload(payload), ensure_ascii=False, separators=(",", ":"))

    def _normalize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """清理不可序列化值，保证日志不会因格式问题丢失。"""
        normalized_payload: dict[str, Any] = {}
        for field_name, field_value in payload.items():
            normalized_payload[field_name] = self._normalize_value(field_value)
        return normalized_payload

    def _normalize_value(self, field_value: Any) -> Any:
        """递归归一化 JSON 值。"""
        if field_value is None or isinstance(field_value, (bool, int, float, str)):
            return field_value
        if isinstance(field_value, list):
            return [self._normalize_value(item) for item in field_value]
        if isinstance(field_value, tuple):
            return [self._normalize_value(item) for item in field_value]
        if isinstance(field_value, dict):
            return {
                str(key): self._normalize_value(value)
                for key, value in field_value.items()
            }
        return str(field_value)
