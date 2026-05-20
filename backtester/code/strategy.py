from __future__ import annotations


def evaluate_trend_following_signal(recent_prices: list[float], trading_period: int) -> bool:
    if len(recent_prices) < trading_period:
        return False
    moving_average = sum(recent_prices[-trading_period:]) / trading_period
    return recent_prices[-1] > moving_average


def build_rebalance_schedule(rows: list[dict], rebalancing_period: str) -> list[bool]:
    months_by_period = {
        "1m": {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12},
        "3m": {3, 6, 9, 12},
        "6m": {6, 12},
        "9m": {9},
        "1y": {12},
    }
    target_months = months_by_period[rebalancing_period]
    flags: list[bool] = []
    for index, row in enumerate(rows):
        next_date = rows[index + 1]["Date"] if index + 1 < len(rows) else None
        is_last_trading_day_of_month = next_date is None or next_date.month != row["Date"].month
        flags.append(is_last_trading_day_of_month and row["Date"].month in target_months)
    return flags


def evaluate_dual_momentum_target(
    rows: list[dict],
    index: int,
    trading_period: int,
    risk_tickers: list[str],
    bond_ticker: str,
) -> dict[str, float]:
    if index < trading_period:
        return {}

    momentum = {
        ticker: rows[index]["prices"][ticker] / rows[index - trading_period]["prices"][ticker] - 1.0
        for ticker in risk_tickers + [bond_ticker]
    }
    risk_momentum = {ticker: momentum[ticker] for ticker in risk_tickers}
    best_risk_ticker = max(risk_momentum, key=risk_momentum.get)
    best_risk_return = risk_momentum[best_risk_ticker]
    bond_return = momentum[bond_ticker]

    if best_risk_return > bond_return:
        return {best_risk_ticker: 1.0}
    if bond_return >= 0.0:
        return {bond_ticker: 1.0}
    return {}
