"""统一日志 handler 与初始化入口。"""

from __future__ import annotations

import logging
import logging.handlers
import os
import socket
import sys

from tf_logging_sdk.config import LoggingConfig
from tf_logging_sdk.filters import ContextEnrichmentFilter
from tf_logging_sdk.formatter import ConsoleFormatter, JsonFormatter
from tf_logging_sdk.masking import LogMasker


class TcpJsonLogstashHandler(logging.Handler):
    """基于 TCP 的简易 JSON Logstash handler。"""

    def __init__(self, host: str, port: int, timeout: float = 1.0):
        """初始化 TCP 输出 handler。

        参数:
            host: Logstash 主机。
            port: Logstash 端口。
            timeout: 连接和发送超时时间，单位秒。
        """
        super().__init__()
        self._host = host
        self._port = port
        self._timeout = timeout

    def emit(self, record: logging.LogRecord) -> None:
        """发送结构化日志，失败时静默降级。"""
        try:
            message = self.format(record) + "\n"
            with socket.create_connection((self._host, self._port), timeout=self._timeout) as client:
                client.sendall(message.encode("utf-8"))
        except Exception:
            self.handleError(record)

    def handleError(self, record: logging.LogRecord) -> None:
        """网络日志失败时不打断主流程。"""
        return


def setup_logging(
    service_name: str,
    environment: str,
    level: str = "INFO",
    enable_stdout: bool = True,
    enable_logstash: bool = True,
    logstash_host: str | None = None,
    logstash_port: int | None = None,
    logstash_timeout: float = 1.0,
    enable_file: bool = False,
    log_file_path: str | None = None,
    file_max_bytes: int = 50 * 1024 * 1024,
    file_backup_count: int = 5,
    mask_fields: list[str] | None = None,
    extra_mask_fields: list[str] | None = None,
) -> LoggingConfig:
    """初始化项目统一日志配置。

    参数:
        service_name: 服务名称。
        environment: 环境名称，例如 dev、test、prod。
        level: 根日志级别。
        enable_stdout: 是否输出到标准输出。
        enable_logstash: 是否启用 Logstash TCP 输出。
        logstash_host: Logstash 主机。
        logstash_port: Logstash 端口。
        logstash_timeout: Logstash 连接超时。
        enable_file: 是否开启文件日志。
        log_file_path: 文件日志路径。
        file_max_bytes: 文件滚动大小上限。
        file_backup_count: 文件备份数量。
        mask_fields: 自定义完整脱敏字段列表。
        extra_mask_fields: 在默认脱敏字段基础上追加的字段。

    返回:
        LoggingConfig: 生效配置对象。
    """
    config = LoggingConfig(
        service_name=service_name,
        environment=environment,
        level=level,
        enable_stdout=enable_stdout,
        enable_logstash=enable_logstash,
        logstash_host=logstash_host,
        logstash_port=logstash_port,
        logstash_timeout=logstash_timeout,
        enable_file=enable_file,
        log_file_path=log_file_path,
        file_max_bytes=file_max_bytes,
        file_backup_count=file_backup_count,
        mask_fields=mask_fields if mask_fields is not None else LoggingConfig(service_name, environment).mask_fields,
        extra_mask_fields=extra_mask_fields or [],
    )
    return _apply_logging_config(config)


def _apply_logging_config(config: LoggingConfig) -> LoggingConfig:
    """将日志配置应用到根 logger。"""
    masker = LogMasker(config.effective_mask_fields)
    root_logger = logging.getLogger()
    root_logger.setLevel(_get_level_value(config.level))
    root_logger.handlers.clear()
    root_logger.filters.clear()

    enrichment_filter = ContextEnrichmentFilter(config=config, masker=masker)

    for handler in _build_handlers(config):
        handler.setLevel(_get_level_value(config.level))
        handler.addFilter(enrichment_filter)
        root_logger.addHandler(handler)

    return config


def _build_handlers(config: LoggingConfig) -> list[logging.Handler]:
    """按配置构建 handler 列表。"""
    handlers: list[logging.Handler] = []

    if config.enable_stdout:
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        stdout_handler.setFormatter(ConsoleFormatter())
        handlers.append(stdout_handler)

    if config.enable_file and config.log_file_path:
        _ensure_log_directory_exists(config.log_file_path)
        file_handler = logging.handlers.RotatingFileHandler(
            filename=config.log_file_path,
            maxBytes=config.file_max_bytes,
            backupCount=config.file_backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(JsonFormatter())
        handlers.append(file_handler)

    if config.enable_logstash and config.logstash_host and config.logstash_port:
        logstash_handler = TcpJsonLogstashHandler(
            host=config.logstash_host,
            port=config.logstash_port,
            timeout=config.logstash_timeout,
        )
        logstash_handler.setFormatter(JsonFormatter())
        handlers.append(logstash_handler)

    if not handlers:
        fallback_handler = logging.StreamHandler(stream=sys.stdout)
        fallback_handler.setFormatter(ConsoleFormatter())
        handlers.append(fallback_handler)

    return handlers


def _ensure_log_directory_exists(log_file_path: str) -> None:
    """确保文件日志目录存在。"""
    directory_path = os.path.dirname(os.path.abspath(log_file_path))
    if directory_path:
        os.makedirs(directory_path, exist_ok=True)


def _get_level_value(level_name: str) -> int:
    """将级别名称转换为 logging 级别值。"""
    level_value = logging.getLevelName(level_name.upper())
    if isinstance(level_value, str):
        raise ValueError("invalid log level")
    return level_value
