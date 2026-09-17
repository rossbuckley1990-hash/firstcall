from __future__ import annotations


def increment(value: int) -> dict[str, int]:
    if not isinstance(value, int):
        raise TypeError("value must be an integer")

    return {"result": value + 1}
