# TradingView Strategy Details

이 문서는 `backtester/strategy.md`를 기준으로 TradingView Pine Script 환경에서 구현할 전략의 판단 규칙과 제약을 정리한다.
Python 백테스터의 원본 전략 정의는 수정하지 않으며, Pine Script에서 구현 가능한 전략만 이 문서에 반영한다.

## Target Strategies

- 구현 대상
  - `trend_following`
  - `dual_momentum`

- 제외 대상
  - `asset_allocation`

- 제외 사유
  - TradingView 전략 엔진은 현재 차트 심볼 중심으로 주문을 처리한다.
  - 여러 ETF를 동시에 목표 비중으로 매수하고 주기적으로 리밸런싱하는 포트폴리오 백테스트는 Python 백테스터가 더 정확하다.
  - Pine Script에서는 자산배분 전략을 신호 표시 수준으로 만들 수는 있지만, 이 프로젝트의 TradingView 작업 범위에서는 제외한다.

## Shared Concepts

- `trading-period`
  - 거래일 기준 판단 기간
  - 추세추종에서는 이동평균 기간
  - 듀얼 모멘텀에서는 모멘텀 비교 기간

- `rebalancing-period`
  - 캘린더 기준 리밸런싱 주기
  - 듀얼 모멘텀에서만 사용
  - 지원값: `1m`, `3m`, `6m`, `9m`, `1y`
  - 실제 판단일은 해당 기간의 마지막 거래일

- 데이터 기준
  - TradingView 차트 데이터와 `request.security()`에서 제공하는 일봉 데이터를 사용
  - Python 백테스터의 CSV 캐시, Yahoo 다운로드, 파일 로그는 사용하지 않음

## Trend Following

- 목적
  - 단일 ETF의 상승 추세만 추종하고 하락 구간은 현금으로 회피

- 투자 대상
  - 현재 차트 심볼 1개

- 판단 규칙
  - `close > trading-period 이동평균`이면 보유
  - `close <= trading-period 이동평균`이면 현금

- 실행 규칙
  - 현재 차트 심볼에 대해 long 진입/청산
  - `rebalancing-period`는 사용하지 않음

- Pine Script 구현 방향
  - `strategy()`로 구현
  - `ta.sma(close, tradingPeriod)` 사용
  - 조건이 참이면 `strategy.entry()`
  - 조건이 거짓이면 `strategy.close()`
  - 이동평균선과 진입/청산 지점을 차트에 표시
  - 진입/청산 시점에는 가격, 이동평균값, `tradingPeriod`를 함께 표시

## Dual Momentum

- 목적
  - 2개의 위험자산 중 상대적으로 강한 자산을 선택하되, 채권보다 약하면 방어적으로 이동

- 투자 대상
  - 위험자산 2개
  - 채권자산 1개

- 판단 규칙
  - 리밸런싱 시점마다 `trading-period` 수익률을 계산
  - 위험자산 2개 중 수익률이 더 높은 자산을 찾음
  - 그 자산의 수익률이 채권 수익률보다 높으면 위험자산 선택
  - 위험자산 2개가 모두 채권보다 낮으면 채권 선택
  - 위험자산과 채권이 모두 음수면 현금 선택

- 실행 규칙
  - 지정한 `rebalancing-period`의 마지막 거래일에만 선택 자산 갱신
  - 선택 결과는 `risk asset`, `bond asset`, `cash` 중 하나

- Pine Script 구현 방향
  - `request.security()`로 비교 대상 심볼의 일봉 가격을 가져옴
  - `close / close[tradingPeriod] - 1` 방식으로 모멘텀 계산
  - 선택된 자산 이름, 모멘텀, 리밸런싱 시점을 차트에 표시
  - 현재 차트 심볼이 선택된 자산과 같을 때만 실제 long 포지션을 잡는 방식으로 구현
  - 리밸런싱 시점에는 이전 선택, 새 선택, 선택 이유, 자산별 모멘텀을 함께 표시

## [Pine script 차이점]

- Pine Script는 로컬 파일 입출력을 지원하지 않음
  - `data/` CSV 캐시 사용 불가
  - `output/backtest.log` 같은 파일 로그 생성 불가

- Pine Script는 TradingView 데이터 피드를 사용함
  - Yahoo Finance 다운로드 로직 없음
  - Python 백테스터와 가격 보정 방식 또는 데이터 이력이 다를 수 있음

- 전략 주문은 현재 차트 심볼 중심임
  - `trend_following`은 Python 전략에 가장 가깝게 구현 가능
  - `dual_momentum`은 자산 선택 로직과 현재 차트 심볼 주문은 구현 가능
  - 선택된 외부 심볼 전체를 실제로 교체 매수하는 포트폴리오 성과는 Python 백테스터처럼 정확히 재현하지 않음

- `asset_allocation`은 TradingView 구현 대상에서 제외
  - 정확한 다중 자산 목표 비중 리밸런싱은 Python 백테스터 기준으로 유지

- 추가 투자금 반영은 Python 백테스터 기준 기능임
  - TradingView `strategy()`에서 매년 첫 거래일 추가 투자금을 Python과 동일하게 재현하지 않음

- 성과 리포트는 TradingView 기본 Strategy Tester를 사용함
  - Python 백테스터의 연도별 성과표, 벤치마크 표, 상세 로그와 동일하게 만들지 않음

- Pine Script의 주요 목적은 전략 신호 시각화와 TradingView 내 빠른 확인임
  - 최종 검증과 재현 가능한 성과 비교는 Python 백테스터를 기준으로 함
