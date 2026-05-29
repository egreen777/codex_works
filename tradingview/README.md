# TradingView Pine Scripts

이 폴더는 Python 백테스터의 전략 중 TradingView Pine Script로 구현 가능한 전략을 관리한다.

## 구현된 전략

- `trend_following`
  - 파일: `tradingview/code/trend_following.pine`
  - 현재 차트 심볼 기준
  - `close > tradingPeriod 이동평균`이면 long, 아니면 cash

- `dual_momentum`
  - 파일: `tradingview/code/dual_momentum.pine`
  - 위험자산 2개와 채권자산 1개의 모멘텀 비교
  - 현재 차트 심볼이 선택 자산과 같을 때만 long
  - 선택 자산이 현금이거나 현재 차트 심볼과 다르면 flat

## 사용 방법

1. TradingView에서 Pine Editor를 연다.
2. 사용할 `.pine` 파일 내용을 붙여 넣는다.
3. Add to chart를 실행한다.
4. Inputs에서 `Trading Period`, ticker, `Rebalancing Period`를 조정한다.

## 기본값

- `Trading Period`: `120`
- `Rebalancing Period`: `3m`

## 주의사항

- TradingView Pine Script는 로컬 CSV, 파일 로그, Python 백테스터의 연도별 성과표를 재현하지 않는다.
- 정확한 다중 자산 포트폴리오 성과 검증은 Python 백테스터를 기준으로 한다.
- Pine Script는 전략 발동 시점과 판단 근거를 차트에 시각화하는 용도로 사용한다.
