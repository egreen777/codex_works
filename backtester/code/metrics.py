from __future__ import annotations

import math


def calculate_max_drawdown(values: list[float]) -> float:
    if not values:
        return 0.0

    running_peak = values[0]
    max_drawdown = 0.0
    for value in values:
        running_peak = max(running_peak, value)
        max_drawdown = min(max_drawdown, value / running_peak - 1.0)
    return max_drawdown


def calculate_average_holding_period(positions: list[bool]) -> float:
    periods: list[int] = []
    current = 0
    for invested in positions:
        if invested:
            current += 1
            continue
        if current:
            periods.append(current)
            current = 0
    if current:
        periods.append(current)
    return sum(periods) / len(periods) if periods else 0.0


def calculate_cagr(growth_multiple: float, total_days: int) -> float:
    if total_days <= 0:
        return 0.0
    if growth_multiple <= 0:
        return -1.0
    return math.pow(growth_multiple, 365.25 / total_days) - 1.0
