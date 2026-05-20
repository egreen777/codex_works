# ETF Backtester

미국 ETF 일봉 데이터를 Yahoo Finance에서 자동 다운로드하고, `backtester/data/`에 CSV로 저장해 재사용하는 CLI 백테스터입니다.

## Folder Layout

- `backtester/code`: 실행 코드
- `backtester/data`: 다운로드한 ETF CSV 데이터
- `backtester/output`: 저장한 리포트 출력물
- `backtester/run_backtest.py`: 실행 진입점

## Strategy

- 구현된 전략: `trend_following`, `dual_momentum`, `asset_allocation`
- `trend_following`: `종가 > trading-period 이동평균이면 보유, 아니면 현금`
- `dual_momentum`: 2개 위험자산과 1개 채권자산을 비교해 리밸런싱일마다 1개 자산 또는 현금을 선택
- `asset_allocation`: 지정한 자산 비중으로 보유하고 리밸런싱일마다 목표 비중으로 재조정
- 벤치마크는 단일 종목 전략이면 해당 종목, 다중 자산 전략이면 `VOO buy and hold` 입니다.
- `annual contribution`은 매년 첫 거래일에 반영됩니다.
- 기본값은 `--trading-period 120`, `--rebalancing-period 3m` 입니다.
- 단, `trend_following` 전략은 `--rebalancing-period`를 사용하지 않으며 입력되면 무시 안내를 출력합니다.

## Supported Tickers

- `VOO`, `SPY`, `SSO`, `SPXL`
- `QQQ`, `QLD`, `TQQQ`
- `EEM`
- `SHY`, `IEF`, `TLT`
- `GLD`, `SLV`, `COPX`

## Run

```bash
cd backtester
python run_backtest.py --strategy trend_following --ticker SPY --start 2018-01-01 --end 2025-01-01 --initial-capital 10000 --annual-contribution 2000
```

듀얼 모멘텀:

```bash
cd backtester
python run_backtest.py --strategy dual_momentum --tickers QQQ:30,VOO:20 --bond-ticker IEF:50 --start 2018-01-01 --end 2025-01-01
```

자산배분:

```bash
cd backtester
python run_backtest.py --strategy asset_allocation --tickers QQQ:40,VOO:25 --bond-ticker IEF --start 2018-01-01 --end 2025-01-01
```

리포트를 파일로 저장하려면:

```bash
cd backtester
python run_backtest.py --strategy trend_following --ticker QQQ --start 2018-01-01 --end 2025-01-01 --save-report qqq_report.txt
```

## Output

- 연도별 전략 성과와 벤치마크 성과
- 연도별 수익률과 연도별 MDD
- 최종 누적수익률, CAGR, 전체 MDD, 평균 보유일수
