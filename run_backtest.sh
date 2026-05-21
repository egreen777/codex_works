#usage: run_backtest.py [-h] [--strategy STRATEGY] [--ticker TICKER] [--tickers TICKERS] [--bond-ticker BOND_TICKER] --start START --end END
#                       [--initial-capital INITIAL_CAPITAL] [--annual-contribution ANNUAL_CONTRIBUTION] [--trading-period TRADING_PERIOD]
#                       [--rebalancing-period REBALANCING_PERIOD] [--save-report SAVE_REPORT]
#run_backtest.py: error: the following arguments are required: --start, --end
#python run_backtest.py --strategy dual_momentum -tickers QQQ,SPY --bond-ticker IEF --start 2014-01-01 --end 2026-04-30 --initial-capital 10000 --annual-contribution 1000 --trading-period 120 --rebalancing-period 6m
#STRTEGY: dual_momentum trend_following asset_allocation

#python backtester/run_backtest.py --strategy asset_allocation --tickers QQQ:30,SPY:40,GLD:10 --bond-ticker IEF --start 2014-01-01 --end 2026-04-30 --initial-capital 10000 --annual-contribution 1000 --trading-period 120 --rebalancing-period 6m
#python backtester/run_backtest.py --strategy asset_allocation --tickers QQQ:20,SPY:50,GLD:10 --bond-ticker IEF --start 2014-01-01 --end 2026-04-30 --initial-capital 10000 --trading-period 120 --rebalancing-period 6m
#python backtester/run_backtest.py --strategy dual_momentum --tickers QQQ,VOO --bond-ticker IEF --start 2014-01-01 --end 2026-04-30 --initial-capital 10000 --trading-period 200 --rebalancing-period 1m
python backtester/run_backtest.py --strategy dual_momentum --tickers QQQ,VOO --bond-ticker IEF --start 2014-01-01 --end 2026-04-30 --initial-capital 10000 --trading-period 200 --rebalancing-period 1m

#python backtester/run_backtest.py --strategy trend_following --ticker VOO --start 2014-01-01 --end 2026-04-30 --initial-capital 10000
