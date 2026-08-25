from __future__ import annotations

from typing import Any, Mapping


def parse_labelled_lines(lines: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in lines:
        label, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"metadata line is not labelled: {line!r}")
        values[label.strip()] = value.strip()
    return values


def required(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if value is None or not str(value).strip():
        raise ValueError(f"required value is missing: {key}")
    return str(value).strip()
