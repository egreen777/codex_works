from __future__ import annotations

from datetime import date

from metrics import calculate_average_holding_period, calculate_cagr, calculate_max_drawdown
from strategy import build_rebalance_schedule, evaluate_dual_momentum_target, evaluate_trend_following_signal


def run_backtest(
    strategy: str,
    aligned_history: list[dict],
    benchmark_history: list[dict],
    effective_start_date: date,
    initial_capital: float,
    annual_contribution: float,
    trading_period: int,
    rebalancing_period: str | None,
    benchmark_ticker: str,
    allocation_weights: dict[str, float] | None = None,
    dual_momentum_tickers: list[str] | None = None,
    bond_ticker: str | None = None,
) -> tuple[list[dict], list[dict], dict, list[str]]:
    if strategy == "trend_following":
        strategy_rows, debug_events = _run_trend_following(
            aligned_history=aligned_history,
            effective_start_date=effective_start_date,
            initial_capital=initial_capital,
            annual_contribution=annual_contribution,
            trading_period=trading_period,
        )
    elif strategy == "dual_momentum":
        strategy_rows, debug_events = _run_dual_momentum(
            aligned_history=aligned_history,
            effective_start_date=effective_start_date,
            initial_capital=initial_capital,
            annual_contribution=annual_contribution,
            trading_period=trading_period,
            rebalancing_period=rebalancing_period or "3m",
            dual_momentum_tickers=dual_momentum_tickers or [],
            bond_ticker=bond_ticker or "",
        )
    elif strategy == "asset_allocation":
        strategy_rows, debug_events = _run_asset_allocation(
            aligned_history=aligned_history,
            effective_start_date=effective_start_date,
            initial_capital=initial_capital,
            annual_contribution=annual_contribution,
            trading_period=trading_period,
            rebalancing_period=rebalancing_period or "3m",
            allocation_weights=allocation_weights or {},
        )
    else:
        raise ValueError(f"Unsupported strategy: {strategy}")

    benchmark_rows = _run_buy_and_hold(
        benchmark_history=benchmark_history,
        effective_start_date=effective_start_date,
        initial_capital=initial_capital,
        annual_contribution=annual_contribution,
    )
    _mark_contribution_days(strategy_rows)
    _mark_contribution_days(benchmark_rows)

    yearly_summary = build_yearly_summary(strategy_rows, benchmark_rows)
    final_summary = build_final_summary(
        strategy_rows=strategy_rows,
        benchmark_rows=benchmark_rows,
        initial_capital=initial_capital,
        annual_contribution=annual_contribution,
        benchmark_ticker=benchmark_ticker,
    )
    return strategy_rows, yearly_summary, final_summary, debug_events


def _run_trend_following(
    aligned_history: list[dict],
    effective_start_date: date,
    initial_capital: float,
    annual_contribution: float,
    trading_period: int,
) -> tuple[list[dict], list[str]]:
    previous_price = None
    previous_year = None
    portfolio_value = initial_capital
    growth_index = 1.0
    current_weight = 0.0
    recent_prices: list[float] = []
    results: list[dict] = []
    debug_events: list[str] = []

    for index, row in enumerate(aligned_history):
        price = float(next(iter(row["prices"].values())))
        in_backtest = row["Date"] >= effective_start_date
        if in_backtest and index > 0 and row["Date"].year != previous_year:
            portfolio_value += annual_contribution

        if in_backtest:
            asset_return = 0.0 if previous_price is None else price / previous_price - 1.0
            strategy_return = current_weight * asset_return
            growth_index *= 1.0 + strategy_return
            portfolio_value *= 1.0 + strategy_return

        recent_prices.append(price)
        signal = evaluate_trend_following_signal(recent_prices, trading_period)
        next_weight = 1.0 if signal else 0.0
        if in_backtest and next_weight != current_weight:
            action = "ENTER" if next_weight > current_weight else "EXIT"
            debug_events.append(
                f"{row['Date'].isoformat()} trend_following {action} price={price:.4f} "
                f"trading_period={trading_period} cum_return={(growth_index - 1.0) * 100:.2f}%"
            )
        if in_backtest:
            results.append(
                {
                    "Date": row["Date"],
                    "portfolio_value": portfolio_value,
                    "growth_index": growth_index,
                    "position": current_weight > 0,
                }
            )

        current_weight = next_weight
        previous_price = price
        previous_year = row["Date"].year

    return results, debug_events


def _run_dual_momentum(
    aligned_history: list[dict],
    effective_start_date: date,
    initial_capital: float,
    annual_contribution: float,
    trading_period: int,
    rebalancing_period: str,
    dual_momentum_tickers: list[str],
    bond_ticker: str,
) -> tuple[list[dict], list[str]]:
    rebalancing_flags = build_rebalance_schedule(aligned_history, rebalancing_period)
    previous_prices: dict[str, float] | None = None
    previous_year = None
    portfolio_value = initial_capital
    growth_index = 1.0
    current_weights: dict[str, float] = {}
    results: list[dict] = []
    debug_events: list[str] = []

    for index, row in enumerate(aligned_history):
        in_backtest = row["Date"] >= effective_start_date
        if in_backtest and index > 0 and row["Date"].year != previous_year:
            portfolio_value += annual_contribution

        if in_backtest:
            asset_returns = _calculate_asset_returns(row["prices"], previous_prices)
            strategy_return = _weighted_return(current_weights, asset_returns)
            growth_index *= 1.0 + strategy_return
            portfolio_value *= 1.0 + strategy_return

        if in_backtest:
            results.append(
                {
                    "Date": row["Date"],
                    "portfolio_value": portfolio_value,
                    "growth_index": growth_index,
                    "position": bool(current_weights),
                }
            )

        if rebalancing_flags[index]:
            previous_selection = _selected_asset_name(current_weights)
            current_weights, decision = evaluate_dual_momentum_target(
                rows=aligned_history,
                index=index,
                trading_period=trading_period,
                risk_tickers=dual_momentum_tickers,
                bond_ticker=bond_ticker,
            )
            momentum = decision["momentum"]
            momentum_text = ", ".join(
                f"{ticker}={float(value) * 100:.2f}%"
                for ticker, value in momentum.items()
            )
            selected = decision.get("selected", "NON")
            debug_events.append(
                f"{row['Date'].isoformat()} dual_momentum sel={previous_selection}->{selected} "
                f"decision={decision['decision']} trad_p={trading_period} "
                f"rebal_p={rebalancing_period} cum_return={(growth_index - 1.0) * 100:.2f}% "
                f"momentum[{momentum_text}]"
            )

        previous_prices = row["prices"]
        previous_year = row["Date"].year

    return results, debug_events


def _run_asset_allocation(
    aligned_history: list[dict],
    effective_start_date: date,
    initial_capital: float,
    annual_contribution: float,
    trading_period: int,
    rebalancing_period: str,
    allocation_weights: dict[str, float],
) -> tuple[list[dict], list[str]]:
    rebalancing_flags = build_rebalance_schedule(aligned_history, rebalancing_period)
    previous_prices: dict[str, float] | None = None
    previous_year = None
    portfolio_value = initial_capital
    growth_index = 1.0
    current_weights: dict[str, float] = {}
    results: list[dict] = []
    debug_events: list[str] = []

    for index, row in enumerate(aligned_history):
        in_backtest = row["Date"] >= effective_start_date
        if in_backtest and index > 0 and row["Date"].year != previous_year:
            portfolio_value += annual_contribution

        if in_backtest:
            asset_returns = _calculate_asset_returns(row["prices"], previous_prices)
            strategy_return = _weighted_return(current_weights, asset_returns)
            growth_index *= 1.0 + strategy_return
            portfolio_value *= 1.0 + strategy_return

        if in_backtest:
            results.append(
                {
                    "Date": row["Date"],
                    "portfolio_value": portfolio_value,
                    "growth_index": growth_index,
                    "position": bool(current_weights),
                }
            )

        if index >= trading_period - 1 and (index == trading_period - 1 or rebalancing_flags[index]):
            current_weights = dict(allocation_weights)
            weights_text = ", ".join(f"{ticker}={weight * 100:.2f}%" for ticker, weight in current_weights.items())
            debug_events.append(
                f"{row['Date'].isoformat()} asset_allocation trad_p={trading_period} "
                f"rebal_p={rebalancing_period} cum_return={(growth_index - 1.0) * 100:.2f}% "
                f"weights[{weights_text}]"
            )

        previous_prices = row["prices"]
        previous_year = row["Date"].year

    return results, debug_events


def _run_buy_and_hold(
    benchmark_history: list[dict],
    effective_start_date: date,
    initial_capital: float,
    annual_contribution: float,
) -> list[dict]:
    previous_price = None
    previous_year = None
    portfolio_value = initial_capital
    growth_index = 1.0
    results: list[dict] = []

    for index, row in enumerate(benchmark_history):
        price = float(next(iter(row["prices"].values())))
        in_backtest = row["Date"] >= effective_start_date
        if in_backtest and index > 0 and row["Date"].year != previous_year:
            portfolio_value += annual_contribution

        if in_backtest:
            benchmark_return = 0.0 if previous_price is None else price / previous_price - 1.0
            growth_index *= 1.0 + benchmark_return
            portfolio_value *= 1.0 + benchmark_return

        if in_backtest:
            results.append(
                {
                    "Date": row["Date"],
                    "portfolio_value": portfolio_value,
                    "growth_index": growth_index,
                    "position": True,
                }
            )

        previous_price = price
        previous_year = row["Date"].year

    return results


def _mark_contribution_days(rows: list[dict]) -> None:
    previous_year = None
    for index, row in enumerate(rows):
        row["is_contribution_day"] = index > 0 and row["Date"].year != previous_year
        previous_year = row["Date"].year


def build_yearly_summary(strategy_rows: list[dict], benchmark_rows: list[dict]) -> list[dict]:
    grouped_strategy = _group_by_year(strategy_rows)
    grouped_benchmark = _group_by_year(benchmark_rows)

    summary: list[dict] = []
    for year in sorted(grouped_strategy):
        strategy_group = grouped_strategy[year]
        benchmark_group = grouped_benchmark[year]
        strategy_start_growth = float(strategy_group[0]["growth_index"])
        benchmark_start_growth = float(benchmark_group[0]["growth_index"])

        summary.append(
            {
                "year": year,
                "end_value": float(strategy_group[-1]["portfolio_value"]),
                "return": _growth_return(strategy_group[-1]["growth_index"], strategy_start_growth),
                "mdd": calculate_max_drawdown([float(item["portfolio_value"]) for item in strategy_group]),
                "bm_value": float(benchmark_group[-1]["portfolio_value"]),
                "bm_return": _growth_return(benchmark_group[-1]["growth_index"], benchmark_start_growth),
                "bm_mdd": calculate_max_drawdown([float(item["portfolio_value"]) for item in benchmark_group]),
            }
        )

    return summary


def build_final_summary(
    strategy_rows: list[dict],
    benchmark_rows: list[dict],
    initial_capital: float,
    annual_contribution: float,
    benchmark_ticker: str,
) -> dict:
    total_days = max((strategy_rows[-1]["Date"] - strategy_rows[0]["Date"]).days, 1)
    contribution_years = sum(1 for row in strategy_rows if row["is_contribution_day"])
    total_contributions = initial_capital + contribution_years * annual_contribution

    strategy_growth = float(strategy_rows[-1]["growth_index"])
    benchmark_growth = float(benchmark_rows[-1]["growth_index"])

    return {
        "start_date": strategy_rows[0]["Date"].isoformat(),
        "end_date": strategy_rows[-1]["Date"].isoformat(),
        "ending_value": float(strategy_rows[-1]["portfolio_value"]),
        "cumulative_return": strategy_growth - 1.0,
        "cagr": calculate_cagr(strategy_growth, total_days),
        "overall_mdd": calculate_max_drawdown([float(item["portfolio_value"]) for item in strategy_rows]),
        "average_holding_days": calculate_average_holding_period([bool(item["position"]) for item in strategy_rows]),
        "benchmark_ticker": benchmark_ticker,
        "benchmark_ending_value": float(benchmark_rows[-1]["portfolio_value"]),
        "benchmark_cumulative_return": benchmark_growth - 1.0,
        "benchmark_cagr": calculate_cagr(benchmark_growth, total_days),
        "benchmark_overall_mdd": calculate_max_drawdown([float(item["portfolio_value"]) for item in benchmark_rows]),
        "total_contributed_capital": total_contributions,
    }


def _group_by_year(rows: list[dict]) -> dict[int, list[dict]]:
    grouped: dict[int, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["Date"].year, []).append(row)
    return grouped


def _growth_return(end_growth: float, start_growth: float) -> float:
    if start_growth == 0:
        return 0.0
    return end_growth / start_growth - 1.0


def _calculate_asset_returns(current_prices: dict[str, float], previous_prices: dict[str, float] | None) -> dict[str, float]:
    if previous_prices is None:
        return {ticker: 0.0 for ticker in current_prices}
    return {
        ticker: current_prices[ticker] / previous_prices[ticker] - 1.0
        for ticker in current_prices
    }


def _weighted_return(weights: dict[str, float], asset_returns: dict[str, float]) -> float:
    return sum(weights.get(ticker, 0.0) * asset_returns.get(ticker, 0.0) for ticker in asset_returns)


def _selected_asset_name(weights: dict[str, float]) -> str:
    if not weights:
        return "CAS"
    return max(weights, key=weights.get)
