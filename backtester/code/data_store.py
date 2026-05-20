from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


CSV_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]


def load_price_history(data_dir: Path, ticker: str, start: str, end: str) -> list[dict[str, Any]]:
    data_dir.mkdir(parents=True, exist_ok=True)
    csv_path = data_dir / f"{ticker}.csv"
    start_date = dt.date.fromisoformat(start)
    end_date = dt.date.fromisoformat(end)

    cached_rows = read_csv(csv_path) if csv_path.exists() else []
    if _covers_range(cached_rows, start_date, end_date):
        return filter_rows(cached_rows, start_date, end_date)

    download_start = min(start_date, cached_rows[0]["Date"]) if cached_rows else start_date
    download_end = max(end_date, cached_rows[-1]["Date"]) if cached_rows else end_date
    downloaded_rows = download_price_history(ticker=ticker, start=download_start.isoformat(), end=download_end.isoformat())

    merged_rows = merge_rows(cached_rows, downloaded_rows)
    write_csv(csv_path, merged_rows)
    return filter_rows(merged_rows, start_date, end_date)


def load_price_histories(data_dir: Path, tickers: list[str], start: str, end: str) -> dict[str, list[dict[str, Any]]]:
    return {ticker: load_price_history(data_dir=data_dir, ticker=ticker, start=start, end=end) for ticker in tickers}


def align_price_histories(price_histories: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    if not price_histories:
        return []

    date_sets = [{row["Date"] for row in rows} for rows in price_histories.values()]
    common_dates = sorted(set.intersection(*date_sets))
    if not common_dates:
        raise ValueError("No overlapping trading dates were found across the selected tickers")

    indexed = {ticker: {row["Date"]: row for row in rows} for ticker, rows in price_histories.items()}
    aligned: list[dict[str, Any]] = []
    for date in common_dates:
        aligned.append(
            {
                "Date": date,
                "prices": {
                    ticker: float(indexed[ticker][date]["Adj Close"])
                    for ticker in price_histories
                },
            }
        )
    return aligned


def read_csv(csv_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                {
                    "Date": dt.date.fromisoformat(row["Date"]),
                    "Open": float(row["Open"]),
                    "High": float(row["High"]),
                    "Low": float(row["Low"]),
                    "Close": float(row["Close"]),
                    "Adj Close": float(row["Adj Close"]),
                    "Volume": int(row["Volume"]),
                }
            )
    return sorted(rows, key=lambda item: item["Date"])


def write_csv(csv_path: Path, rows: list[dict[str, Any]]) -> None:
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "Date": row["Date"].isoformat(),
                    "Open": row["Open"],
                    "High": row["High"],
                    "Low": row["Low"],
                    "Close": row["Close"],
                    "Adj Close": row["Adj Close"],
                    "Volume": row["Volume"],
                }
            )


def filter_rows(rows: list[dict[str, Any]], start_date: dt.date, end_date: dt.date) -> list[dict[str, Any]]:
    return [dict(row) for row in rows if start_date <= row["Date"] <= end_date]


def merge_rows(existing_rows: list[dict[str, Any]], new_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[dt.date, dict[str, Any]] = {row["Date"]: dict(row) for row in existing_rows}
    for row in new_rows:
        merged[row["Date"]] = dict(row)
    return [merged[date] for date in sorted(merged)]


def _covers_range(rows: list[dict[str, Any]], start_date: dt.date, end_date: dt.date) -> bool:
    if not rows:
        return False
    return rows[0]["Date"] <= start_date and rows[-1]["Date"] >= end_date


def _to_unix_timestamp(date_text: str) -> int:
    parsed = dt.datetime.strptime(date_text, "%Y-%m-%d")
    return int(parsed.replace(tzinfo=dt.timezone.utc).timestamp())


def download_price_history(ticker: str, start: str, end: str) -> list[dict[str, Any]]:
    period1 = _to_unix_timestamp(start)
    period2 = _to_unix_timestamp(end) + 86400
    query = urlencode(
        {
            "period1": period1,
            "period2": period2,
            "interval": "1d",
            "includeAdjustedClose": "true",
            "events": "div,splits",
        }
    )

    payload = None
    last_error: Exception | None = None
    for base_url in ("https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com"):
        request = Request(
            f"{base_url}/v8/finance/chart/{ticker}?{query}",
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
        )
        try:
            with urlopen(request) as response:
                payload = json.load(response)
                break
        except (HTTPError, URLError) as exc:
            last_error = exc

    if payload is None:
        raise ValueError(f"Failed to download data from Yahoo Finance for {ticker}: {last_error}")

    chart = payload.get("chart", {})
    if chart.get("error"):
        raise ValueError(f"Yahoo Finance error for {ticker}: {chart['error']}")

    result = chart.get("result")
    if not result:
        raise ValueError(f"No price data returned for ticker={ticker}, start={start}, end={end}")

    data = result[0]
    timestamps = data.get("timestamp") or []
    quote = (data.get("indicators") or {}).get("quote", [{}])[0]
    adjclose = (data.get("indicators") or {}).get("adjclose", [{}])[0].get("adjclose", [])

    rows: list[dict[str, Any]] = []
    for index, timestamp in enumerate(timestamps):
        open_price = _get_series_value(quote.get("open"), index)
        high_price = _get_series_value(quote.get("high"), index)
        low_price = _get_series_value(quote.get("low"), index)
        close_price = _get_series_value(quote.get("close"), index)
        adj_close = _get_series_value(adjclose, index, fallback=close_price)
        volume = _get_series_value(quote.get("volume"), index, fallback=0)

        if None in (open_price, high_price, low_price, close_price):
            continue

        rows.append(
            {
                "Date": dt.datetime.utcfromtimestamp(timestamp).date(),
                "Open": float(open_price),
                "High": float(high_price),
                "Low": float(low_price),
                "Close": float(close_price),
                "Adj Close": float(adj_close),
                "Volume": int(volume or 0),
            }
        )

    if not rows:
        raise ValueError(f"No usable daily bars returned for ticker={ticker}, start={start}, end={end}")
    return rows


def _get_series_value(series: list[Any] | None, index: int, fallback: Any = None) -> Any:
    if series is None or index >= len(series):
        return fallback
    value = series[index]
    return fallback if value is None else value
