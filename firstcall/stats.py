from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class Rate:
    successes: int
    determinate: int
    unknown: int
    rate: float | None
    low: float | None
    high: float | None


def wilson(
    successes: int,
    n: int,
    z: float = 1.959963984540054,
) -> tuple[float, float] | tuple[None, None]:
    if n == 0:
        return None, None

    p = successes / n
    z2 = z * z

    denominator = 1 + z2 / n

    centre = (
        p + z2 / (2 * n)
    ) / denominator

    margin = (
        z
        * sqrt(
            (p * (1 - p) / n)
            + z2 / (4 * n * n)
        )
        / denominator
    )

    return (
        max(0.0, centre - margin),
        min(1.0, centre + margin),
    )


def afcr(
    successes: int,
    determinate: int,
    unknown: int,
) -> Rate:
    if determinate == 0:
        return Rate(
            successes,
            determinate,
            unknown,
            None,
            None,
            None,
        )

    low, high = wilson(
        successes,
        determinate,
    )

    return Rate(
        successes=successes,
        determinate=determinate,
        unknown=unknown,
        rate=successes / determinate,
        low=low,
        high=high,
    )
