from __future__ import annotations

import argparse
import sys
from datetime import date
from datetime import datetime
from datetime import timedelta
from pathlib import Path

from config import (
    DEFAULT_ANNUAL_CONTRIBUTION,
    DEFAULT_INITIAL_CAPITAL,
    DEFAULT_LONG_WINDOW,
    DEFAULT_REBALANCING_PERIOD,
    STRATEGY_METADATA,
    SUPPORTED_REBALANCING_PERIODS,
    SUPPORTED_STRATEGIES,
    SUPPORTED_TICKERS,
)
from data_store import align_price_histories, load_price_histories
from engine import run_backtest
from report import render_final_performance, render_yearly_performance


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backtest US ETF strategies.")
    parser.add_argument(
        "--strategy",
        default="trend_following",
        help="Strategy name. Supported: trend_following, dual_momentum, asset_allocation",
    )
    parser.add_argument("--ticker", help="Single ETF ticker symbol for trend_following")
    parser.add_argument("--tickers", help="Comma-separated tickers with optional weights, for example QQQ:40,VOO:25")
    parser.add_argument("--bond-ticker", help="Bond ticker with optional weight, for example IEF or IEF:35")
    parser.add_argument("--start", required=True, help="Backtest start date in YYYY-MM-DD format")
    parser.add_argument("--end", required=True, help="Backtest end date in YYYY-MM-DD format")
    parser.add_argument("--initial-capital", type=float, default=DEFAULT_INITIAL_CAPITAL, help="Initial cash amount")
    parser.add_argument(
        "--annual-contribution",
        type=float,
        default=DEFAULT_ANNUAL_CONTRIBUTION,
        help="Additional capital added on the first trading day of each new year",
    )
    parser.add_argument(
        "--trading-period",
        type=int,
        default=DEFAULT_LONG_WINDOW,
        help="Trading-day period used by the selected strategy",
    )
    parser.add_argument(
        "--rebalancing-period",
        default=DEFAULT_REBALANCING_PERIOD,
        help="Calendar-based rebalancing period. Supported: 1m, 3m, 6m, 9m, 1y",
    )
    parser.add_argument("--save-report", help="Optional filename to save the report under backtester/output/")
    return parser


def main(project_root: Path | None = None) -> None:
    parser = build_parser()
    argv = sys.argv[1:]
    args = parser.parse_args(argv)

    strategy = validate_strategy(args.strategy)
    root_dir = project_root or Path(__file__).resolve().parents[1]
    data_dir = root_dir / "data"
    output_dir = root_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    ignored_messages = validate_strategy_parameters(
        strategy=strategy,
        rebalancing_period=args.rebalancing_period,
        rebalancing_period_provided="--rebalancing-period" in argv,
        ticker=args.ticker,
        tickers=args.tickers,
        bond_ticker=args.bond_ticker,
    )

    if strategy == "trend_following":
        ticker = validate_ticker_required(args.ticker)
        strategy_tickers = [ticker]
        benchmark_ticker = ticker
        allocation_weights = None
        dual_momentum_tickers = None
        bond_ticker = None
        display_assets = ticker
        rule_code = f"trend_following_close_above_{args.trading_period}d_sma"
    elif strategy == "dual_momentum":
        risk_assets = parse_weighted_ticker_list(args.tickers, allow_missing_weight=True)
        if len(risk_assets) != 2:
            raise SystemExit("dual_momentum requires exactly 2 tickers in --tickers")
        bond_asset = parse_weighted_ticker(args.bond_ticker, allow_missing_weight=True)
        strategy_tickers = [item["ticker"] for item in risk_assets] + [bond_asset["ticker"]]
        benchmark_ticker = "VOO"
        allocation_weights = None
        dual_momentum_tickers = [item["ticker"] for item in risk_assets]
        bond_ticker = bond_asset["ticker"]
        display_assets = ", ".join(strategy_tickers)
        rule_code = f"dual_momentum_{args.trading_period}d_{args.rebalancing_period}"
        ignored_messages.extend(_build_weight_ignored_messages(risk_assets, bond_asset))
    else:
        asset_specs = parse_weighted_ticker_list(args.tickers, allow_missing_weight=True)
        bond_asset = parse_weighted_ticker(args.bond_ticker, allow_missing_weight=True)
        all_assets = asset_specs + [bond_asset]
        strategy_tickers = [item["ticker"] for item in all_assets]
        benchmark_ticker = "VOO"
        allocation_weights = normalize_weights(all_assets)
        dual_momentum_tickers = None
        bond_ticker = None
        display_assets = ", ".join(f"{ticker}:{weight * 100:.2f}" for ticker, weight in allocation_weights.items())
        rule_code = f"asset_allocation_{args.trading_period}d_{args.rebalancing_period}"

    benchmark_needed = sorted(set(strategy_tickers + [benchmark_ticker]))
    requested_start_date = date.fromisoformat(args.start)
    fetch_start_date = requested_start_date - timedelta(days=365)
    aligned_histories = align_price_histories(
        load_price_histories(
            data_dir=data_dir,
            tickers=benchmark_needed,
            start=fetch_start_date.isoformat(),
            end=args.end,
        )
    )
    strategy_history = _subset_aligned_history(aligned_histories, strategy_tickers)
    benchmark_history = _subset_aligned_history(aligned_histories, [benchmark_ticker])

    _, yearly_summary, final_summary, debug_events = run_backtest(
        strategy=strategy,
        aligned_history=strategy_history,
        benchmark_history=benchmark_history,
        effective_start_date=requested_start_date,
        initial_capital=args.initial_capital,
        annual_contribution=args.annual_contribution,
        trading_period=args.trading_period,
        rebalancing_period=args.rebalancing_period,
        benchmark_ticker=benchmark_ticker,
        allocation_weights=allocation_weights,
        dual_momentum_tickers=dual_momentum_tickers,
        bond_ticker=bond_ticker,
    )

    metadata = STRATEGY_METADATA[strategy]
    report_lines = [
        "MY BACKTESTING REPORT",
        "",
        f"Strategy: {metadata['name']}",
        f"Strategy Detail: {metadata['description']}",
        f"Assets: {display_assets}",
        f"Benchmark: {benchmark_ticker} buy_and_hold",
        f"Rule Code: {rule_code}",
        f"Trading Period: {args.trading_period}",
        f"Initial capital: ${args.initial_capital:,.2f}",
        f"Annual contribution: ${args.annual_contribution:,.2f}",
    ]
    if strategy != "trend_following":
        report_lines.append(f"Rebalancing Period: {args.rebalancing_period}")
    if ignored_messages:
        report_lines.append("")
        report_lines.extend(ignored_messages)
    report_lines.extend(["", render_yearly_performance(yearly_summary), "", render_final_performance(final_summary)])
    report_text = "\n".join(report_lines)
    print(report_text)
    write_backtest_log(
        output_dir=output_dir,
        strategy=strategy,
        start=args.start,
        end=args.end,
        assets=display_assets,
        benchmark_ticker=benchmark_ticker,
        trading_period=args.trading_period,
        rebalancing_period=args.rebalancing_period if strategy != "trend_following" else None,
        initial_capital=args.initial_capital,
        annual_contribution=args.annual_contribution,
        ignored_messages=ignored_messages,
        final_summary=final_summary,
        debug_events=debug_events,
    )

    if args.save_report:
        target = output_dir / args.save_report
        target.write_text(report_text + "\n", encoding="utf-8")


def validate_strategy(strategy: str) -> str:
    normalized = strategy.strip().lower()
    if normalized not in SUPPORTED_STRATEGIES:
        supported = ", ".join(SUPPORTED_STRATEGIES)
        raise SystemExit(f"Unsupported strategy: {normalized}. Supported strategies: {supported}")
    return normalized


def validate_ticker_required(ticker: str | None) -> str:
    if not ticker:
        raise SystemExit("trend_following requires --ticker")
    normalized = ticker.upper()
    if normalized not in SUPPORTED_TICKERS:
        supported = ", ".join(SUPPORTED_TICKERS)
        raise SystemExit(f"Unsupported ticker: {normalized}. Supported tickers: {supported}")
    return normalized


def validate_ticker(ticker: str) -> str:
    normalized = ticker.upper()
    if normalized not in SUPPORTED_TICKERS:
        supported = ", ".join(SUPPORTED_TICKERS)
        raise SystemExit(f"Unsupported ticker: {normalized}. Supported tickers: {supported}")
    return normalized


def validate_strategy_parameters(
    strategy: str,
    rebalancing_period: str | None,
    rebalancing_period_provided: bool,
    ticker: str | None,
    tickers: str | None,
    bond_ticker: str | None,
) -> list[str]:
    messages: list[str] = []
    if rebalancing_period and rebalancing_period not in SUPPORTED_REBALANCING_PERIODS:
        supported = ", ".join(SUPPORTED_REBALANCING_PERIODS)
        raise SystemExit(f"Unsupported rebalancing period: {rebalancing_period}. Supported values: {supported}")
    if strategy == "trend_following":
        if tickers:
            messages.append("selected strategy does not use --tickers; parameter was ignored")
        if bond_ticker:
            messages.append("selected strategy does not use --bond-ticker; parameter was ignored")
        if rebalancing_period and rebalancing_period_provided:
            messages.append("selected strategy does not use --rebalancing-period; parameter was ignored")
    else:
        if ticker:
            messages.append("selected strategy does not use --ticker; parameter was ignored")
        if not tickers:
            raise SystemExit(f"{strategy} requires --tickers")
        if not bond_ticker:
            raise SystemExit(f"{strategy} requires --bond-ticker")
    return messages


def parse_weighted_ticker_list(raw_value: str | None, allow_missing_weight: bool) -> list[dict[str, float | None | str]]:
    if not raw_value:
        return []
    return [parse_weighted_ticker(item.strip(), allow_missing_weight=allow_missing_weight) for item in raw_value.split(",")]


def parse_weighted_ticker(raw_value: str | None, allow_missing_weight: bool) -> dict[str, float | None | str]:
    if not raw_value:
        raise SystemExit("Missing ticker value")
    ticker_text, separator, weight_text = raw_value.strip().partition(":")
    ticker = validate_ticker(ticker_text.strip())
    if not separator:
        if not allow_missing_weight:
            raise SystemExit(f"Weight is required for {ticker}")
        return {"ticker": ticker, "weight": None}

    weight = float(weight_text)
    if weight < 0 or weight > 100:
        raise SystemExit(f"Weight must be between 0 and 100 for {ticker}")
    return {"ticker": ticker, "weight": weight}


def normalize_weights(items: list[dict[str, float | None | str]]) -> dict[str, float]:
    explicit_total = sum(float(item["weight"]) for item in items if item["weight"] is not None)
    unspecified = [item for item in items if item["weight"] is None]
    if explicit_total > 100:
        raise SystemExit("Specified weights exceed 100")
    remainder = 100.0 - explicit_total
    if not unspecified and abs(remainder) > 1e-9:
        raise SystemExit("Weights must sum to 100 when all weights are specified")
    fill_weight = remainder / len(unspecified) if unspecified else 0.0

    weights: dict[str, float] = {}
    for item in items:
        weight = float(item["weight"]) if item["weight"] is not None else fill_weight
        weights[str(item["ticker"])] = weight / 100.0
    return weights


def _build_weight_ignored_messages(
    risk_assets: list[dict[str, float | None | str]],
    bond_asset: dict[str, float | None | str],
) -> list[str]:
    messages: list[str] = []
    has_weight = any(item["weight"] is not None for item in risk_assets) or bond_asset["weight"] is not None
    if has_weight:
        messages.append("selected strategy does not use ticker weights; weights in --tickers and --bond-ticker were ignored")
    return messages


def _subset_aligned_history(rows: list[dict], tickers: list[str]) -> list[dict]:
    return [
        {
            "Date": row["Date"],
            "prices": {ticker: row["prices"][ticker] for ticker in tickers},
        }
        for row in rows
    ]


def write_backtest_log(
    output_dir: Path,
    strategy: str,
    start: str,
    end: str,
    assets: str,
    benchmark_ticker: str,
    trading_period: int,
    rebalancing_period: str | None,
    initial_capital: float,
    annual_contribution: float,
    ignored_messages: list[str],
    final_summary: dict,
    debug_events: list[str],
) -> None:
    log_path = output_dir / "backtest.log"
    timestamp = datetime.now().isoformat(timespec="seconds")
    debug_block = _insert_backtest_markers(debug_events, start)
    lines = [
        f"[{timestamp}] strategy={strategy} period={start}->{end}",
        f"assets={assets}",
        f"benchmark={benchmark_ticker}",
        f"trading_period={trading_period}",
        f"rebalancing_period={rebalancing_period or 'n/a'}",
        f"initial_capital={initial_capital:.2f}",
        f"annual_contribution={annual_contribution:.2f}",
        f"ending_value={float(final_summary['ending_value']):.2f}",
        f"cumulative_return={float(final_summary['cumulative_return']) * 100:.2f}%",
        f"overall_mdd={float(final_summary['overall_mdd']) * 100:.2f}%",
    ]
    for message in ignored_messages:
        lines.append(f"ignored={message}")
    if debug_block:
        lines.append("events:")
        lines.extend(f"  {event}" for event in debug_block)
    lines.append("")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def _insert_backtest_markers(debug_events: list[str], start: str) -> list[str]:
    if not debug_events:
        return []

    start_date = date.fromisoformat(start)
    marked: list[str] = []
    start_inserted = False

    for event in debug_events:
        event_date = _extract_event_date(event)
        if not start_inserted and event_date is not None and event_date >= start_date:
            marked.append("--- start ---")
            start_inserted = True
        marked.append(event)

    if not start_inserted:
        marked.append("--- start ---")
    marked.append("--- end ---")
    return marked


def _extract_event_date(event: str) -> date | None:
    if len(event) < 10:
        return None
    try:
        return date.fromisoformat(event[:10])
    except ValueError:
        return None
