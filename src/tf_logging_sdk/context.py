"""统一日志上下文管理。"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from tf_logging_sdk.config import DEFAULT_CONTEXT_FIELDS

_LOG_CONTEXT: ContextVar[dict[str, Any]] = ContextVar("tf_logging_sdk_context", default={})


def bind_log_context(**kwargs: Any) -> None:
    """绑定当前执行上下文的日志字段。

    参数:
        **kwargs: 允许传入标准上下文字段，也允许传入扩展字段。
    """
    current_context = dict(_LOG_CONTEXT.get())
    for field_name, field_value in kwargs.items():
        if field_value is None:
            continue
        current_context[field_name] = field_value
    _LOG_CONTEXT.set(current_context)


def clear_log_context(*field_names: str) -> None:
    """清理当前执行上下文的日志字段。

    参数:
        *field_names: 指定要清理的字段；若为空，则清理全部上下文。
    """
    if not field_names:
        _LOG_CONTEXT.set({})
        return

    current_context = dict(_LOG_CONTEXT.get())
    for field_name in field_names:
        current_context.pop(field_name, None)
    _LOG_CONTEXT.set(current_context)


def get_log_context() -> dict[str, Any]:
    """获取当前执行上下文的日志字段快照。"""
    current_context = dict(_LOG_CONTEXT.get())
    normalized_context: dict[str, Any] = {}
    for field_name in DEFAULT_CONTEXT_FIELDS:
        normalized_context[field_name] = current_context.get(field_name)
    for field_name, field_value in current_context.items():
        if field_name not in normalized_context:
            normalized_context[field_name] = field_value
    return normalized_context
