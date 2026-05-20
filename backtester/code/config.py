SUPPORTED_TICKERS = [
    "VOO",
    "SPY",
    "SSO",
    "SPXL",
    "QQQ",
    "QLD",
    "TQQQ",
    "EEM",
    "SHY",
    "IEF",
    "TLT",
    "GLD",
    "SLV",
    "COPX",
]

DEFAULT_INITIAL_CAPITAL = 10_000.0
DEFAULT_ANNUAL_CONTRIBUTION = 0.0
DEFAULT_LONG_WINDOW = 120
DEFAULT_REBALANCING_PERIOD = "3m"
SUPPORTED_STRATEGIES = ["trend_following", "dual_momentum", "asset_allocation"]
SUPPORTED_REBALANCING_PERIODS = ["1m", "3m", "6m", "9m", "1y"]

STRATEGY_METADATA = {
    "trend_following": {
        "name": "Trend Following",
        "description": (
            "Buy when the adjusted close is above the moving average defined by --trading-period. "
            "Move to cash when it falls at or below that moving average. "
            "Signals are evaluated at today's close and applied on the next trading day."
        ),
    },
    "dual_momentum": {
        "name": "Dual Momentum",
        "description": (
            "Compare the trading-period return of two risk assets against the bond asset on each rebalance date. "
            "Hold the stronger risk asset when it beats the bond asset, otherwise hold the bond asset. "
            "If all momentum values are negative, hold cash."
        ),
    },
    "asset_allocation": {
        "name": "Asset Allocation",
        "description": (
            "Hold the selected assets by target weights and rebalance to the target mix on each rebalancing date. "
            "When a weight is omitted, the remaining weight is filled automatically."
        ),
    },
}
