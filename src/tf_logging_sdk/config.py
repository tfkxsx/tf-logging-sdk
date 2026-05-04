"""统一日志 SDK 配置定义。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DEFAULT_STANDARD_FIELDS = [
    "timestamp",
    "level",
    "service",
    "environment",
    "module",
    "message",
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
    "error",
]

DEFAULT_MASK_FIELDS = [
    "password",
    "token",
    "authorization",
    "cookie",
    "secret",
    "access_key",
    "proxy_password",
    "phone",
    "email",
]

DEFAULT_CONTEXT_FIELDS = [
    "trace_id",
    "task_id",
    "space_id",
    "message_type",
    "topic",
    "consumer_group",
    "worker_type",
    "region",
]

DEFAULT_EXTRA_FIELDS = [
    "duration_ms",
    "error_code",
    "error",
]

RESERVED_LOG_RECORD_FIELDS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "taskName",
    "thread",
    "threadName",
}


@dataclass(slots=True)
class LoggingConfig:
    """统一日志初始化配置。"""

    service_name: str
    environment: str
    level: str = "INFO"
    enable_stdout: bool = True
    enable_logstash: bool = True
    logstash_host: str | None = None
    logstash_port: int | None = None
    logstash_timeout: float = 1.0
    enable_file: bool = False
    log_file_path: str | None = None
    file_max_bytes: int = 50 * 1024 * 1024
    file_backup_count: int = 5
    standard_fields: list[str] = field(default_factory=lambda: list(DEFAULT_STANDARD_FIELDS))
    mask_fields: list[str] = field(default_factory=lambda: list(DEFAULT_MASK_FIELDS))
    extra_mask_fields: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """校验并整理配置。"""
        if not self.service_name:
            raise ValueError("service_name is required")
        if not self.environment:
            raise ValueError("environment is required")
        if self.enable_file and not self.log_file_path:
            raise ValueError("log_file_path is required when enable_file is True")
        if self.file_max_bytes <= 0:
            raise ValueError("file_max_bytes must be greater than 0")
        if self.file_backup_count < 0:
            raise ValueError("file_backup_count must be greater than or equal to 0")
        self.level = self.level.upper()

    @property
    def effective_mask_fields(self) -> list[str]:
        """返回最终生效的脱敏字段列表。"""
        mask_field_map = {field_name.lower(): field_name for field_name in self.mask_fields}
        for field_name in self.extra_mask_fields:
            mask_field_map[field_name.lower()] = field_name
        return list(mask_field_map.values())

    @classmethod
    def from_kwargs(cls, **kwargs: Any) -> "LoggingConfig":
        """兼容关键字参数初始化。"""
        return cls(**kwargs)
