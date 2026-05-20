# Strategy Definitions

## Shared Parameters

- `--trading-period`: trading-day based period
- Meaning in trend following: moving-average length
- Meaning in dual momentum: price lookback window for momentum comparison
- Meaning in asset allocation: price lookback window used for allocation decisions
- `--rebalancing-period`: calendar-based rebalance schedule
- Supported values: `1m`, `3m`, `6m`, `9m`, `1y`
- Execution day: the last trading day of the selected calendar period
- If a selected strategy does not use this parameter, the tool reports that it was ignored

## Trend Following

- Scope: first implemented strategy
- Uses `--trading-period`
- Does not use `--rebalancing-period`
- Rule: buy when the adjusted close is above the moving average defined by `--trading-period`
- Exit: move to cash when the adjusted close is at or below that moving average
- Execution timing: generate the signal at today's close and apply the position on the next trading day
- Universe: single ETF in the first version

## Dual Momentum

- Scope: implemented strategy
- Uses `--trading-period` as momentum lookback window
- Uses `--rebalancing-period` as rebalance schedule
- Input format: `--tickers QQQ:30,VOO:20 --bond-ticker IEF:50`
- Weight note: weights in the input are accepted for a consistent CLI shape, but this strategy currently invests 100% in one selected asset at a time
- Rule: compare two equity assets and choose the one with stronger momentum when it is stronger than the bond proxy
- Fallback: if both equity assets are weaker than the bond proxy, hold the bond asset
- Cash condition: if both equity assets and the bond proxy are negative, hold cash

## Asset Allocation

- Scope: implemented strategy
- Uses `--trading-period` as price evaluation window
- Uses `--rebalancing-period` as rebalance schedule
- Input format: `--tickers QQQ:40,VOO:25 --bond-ticker IEF`
- Rule: choose one equity asset, one bond asset, and one alternative asset, then buy by target weights
- Default weighting: use equal weight when no explicit ratio is provided
- Remaining weight rule: if some weights are missing, the remaining percentage is distributed equally across the unspecified assets
- Rebalance timing: rebalance back to the target weights on the last trading day of each selected calendar period
