"""统一日志脱敏能力。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

MASK_PLACEHOLDER = "***"


class LogMasker:
    """日志脱敏器。"""

    def __init__(self, mask_fields: list[str]):
        """初始化脱敏器。

        参数:
            mask_fields: 需要按字段名脱敏的字段列表。
        """
        self._mask_fields = {field_name.lower() for field_name in mask_fields}

    def mask(self, value: Any, field_name: str | None = None) -> Any:
        """对任意对象进行递归脱敏。

        参数:
            value: 待脱敏对象。
            field_name: 当前对象对应的字段名。

        返回:
            Any: 脱敏后的对象。
        """
        if field_name and field_name.lower() in self._mask_fields:
            return self._mask_scalar(value)
        if isinstance(value, Mapping):
            return {
                key: self.mask(item, field_name=str(key))
                for key, item in value.items()
            }
        if isinstance(value, tuple):
            return tuple(self.mask(item) for item in value)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return [self.mask(item) for item in value]
        return value

    def mask_text(self, text: str) -> str:
        """对纯文本执行轻量脱敏。

        参数:
            text: 待处理文本。

        返回:
            str: 脱敏后的文本。
        """
        masked_text = text
        for field_name in self._mask_fields:
            lower_text = masked_text.lower()
            if field_name not in lower_text:
                continue

            token_patterns = [
                f"{field_name}=",
                f"{field_name}:",
                f"'{field_name}':",
                f'"{field_name}":',
            ]
            for token_pattern in token_patterns:
                masked_text = self._mask_text_pattern(masked_text, token_pattern)
        return masked_text

    def _mask_text_pattern(self, text: str, marker: str) -> str:
        """按标记符号对文本片段脱敏。"""
        search_start = 0
        masked_text = text
        marker_length = len(marker)
        while True:
            match_index = masked_text.lower().find(marker.lower(), search_start)
            if match_index < 0:
                break
            value_start = match_index + marker_length
            value_end = self._locate_value_end(masked_text, value_start)
            original_value = masked_text[value_start:value_end].strip().strip("'\"")
            if original_value:
                masked_value = self._mask_scalar(original_value)
                masked_text = (
                    masked_text[:value_start]
                    + f" {masked_value}"
                    + masked_text[value_end:]
                )
                search_start = value_start + len(str(masked_value)) + 1
            else:
                search_start = value_end
        return masked_text

    @staticmethod
    def _locate_value_end(text: str, value_start: int) -> int:
        """定位文本值的结束位置。"""
        separators = [",", ";", "&", " ", "\n", "\r", "\t", "}"]
        positions = [text.find(separator, value_start) for separator in separators]
        valid_positions = [position for position in positions if position >= 0]
        if not valid_positions:
            return len(text)
        return min(valid_positions)

    @staticmethod
    def _mask_scalar(value: Any) -> str:
        """对标量值脱敏，仅保留少量首尾信息。"""
        value_text = str(value)
        if not value_text:
            return MASK_PLACEHOLDER
        if len(value_text) <= 6:
            return MASK_PLACEHOLDER
        return f"{value_text[:2]}{MASK_PLACEHOLDER}{value_text[-2:]}"
