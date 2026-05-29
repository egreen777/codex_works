# Pine Script Build Guide

이 문서는 `tradingview/strategy.md`에 정의한 전략을 TradingView Pine Script로 구현할 때 따라야 하는 개발 지침을 정리한다.
목적은 Python 백테스터와 역할을 분리하면서도 Pine Script에서 구현 가능한 전략을 일관되게 유지하는 것이다.

## Scope

- 대상 시장: 미국 ETF
- 데이터 주기: 일봉
- 실행 환경: TradingView Pine Script
- 구현 대상 전략: `trend_following`, `dual_momentum`
- 제외 전략: `asset_allocation`
- 주요 목적: 전략 신호 시각화, TradingView Strategy Tester 기반 빠른 확인
- 최종 성과 검증 기준: Python 백테스터

## Project Structure

- `tradingview/README.md`
  - 사용자가 Pine Script를 TradingView에서 사용하는 방법

- `tradingview/strategy.md`
  - TradingView 환경에 맞춘 전략 정의

- `tradingview/pine_build.md`
  - Pine Script 구현 지침

- `tradingview/code/*.pine`
  - 전략별 Pine Script 파일

## Source Of Truth

- 원본 전략 정의는 `backtester/strategy.md`를 참고
- TradingView 제약으로 인해 달라지는 내용은 `tradingview/strategy.md`의 `[Pine script 차이점]` 섹션에 기록
- Python 백테스터 파일은 TradingView 세션에서 수정하지 않음
- `asset_allocation`은 Pine Script 구현 대상에서 제외하고 Python 백테스터 기준으로 유지

## Pine Version

- Pine Script는 최신 안정 버전 기준으로 작성
- 새 파일은 `//@version=6`을 기본으로 사용
- TradingView 호환성 문제가 있으면 해당 파일에서만 필요한 최소 수정으로 대응

## Data Rules

- TradingView 차트 데이터와 `request.security()`를 사용
- 외부 CSV, Yahoo Finance 다운로드, 로컬 캐시를 사용하지 않음
- 계산 기준은 Pine Script에서 접근 가능한 가격 기준을 사용
- 기본 타임프레임은 일봉
- 다른 타임프레임 지원은 사용자가 명시적으로 요청하기 전까지 추가하지 않음

## Input Rules

- 공통 입력
  - `tradingPeriod`

- `dual_momentum` 입력
  - 위험자산 1번 ticker
  - 위험자산 2번 ticker
  - 채권자산 ticker
  - `rebalancingPeriod`

- 기본값
  - `tradingPeriod = 120`
  - `rebalancingPeriod = 3m`

- `rebalancingPeriod` 허용값
  - `1m`
  - `3m`
  - `6m`
  - `9m`
  - `1y`

- `trend_following`은 `rebalancingPeriod`를 사용하지 않음

## Strategy Implementation Rules

- `trend_following`
  - `strategy()`로 구현
  - 현재 차트 심볼을 거래 대상으로 사용
  - `close > ta.sma(close, tradingPeriod)`이면 long
  - 조건이 false면 position close
  - 이동평균선, 매수 지점, 청산 지점을 표시

- `dual_momentum`
  - `request.security()`로 위험자산 2개와 채권자산 1개의 일봉 가격을 가져옴
  - `tradingPeriod` 기준 수익률로 모멘텀을 계산
  - 리밸런싱 날짜에만 선택 자산을 갱신
  - 선택 결과는 차트 라벨, plot, table로 표시
  - 현재 차트 심볼이 선택 자산과 같을 때만 `strategy.entry()` 실행
  - 선택 자산이 현금이거나 현재 차트 심볼과 다르면 `strategy.close()` 실행

## Rebalancing Rules

- `1m`: 매월 마지막 거래일
- `3m`: 3, 6, 9, 12월 마지막 거래일
- `6m`: 6, 12월 마지막 거래일
- `9m`: 9월 마지막 거래일
- `1y`: 12월 마지막 거래일

- Pine Script에서는 다음 봉의 월/연도 변화를 이용해 마지막 거래일을 판단
- 휴일은 TradingView 거래일 데이터에 의해 자연스럽게 직전 거래일로 처리됨

## Visualization Rules

- 차트에는 전략 상태를 명확히 표시
- 최소 표시 항목
  - 현재 선택 자산
  - 모멘텀 값
  - 리밸런싱 발생 여부
  - 매수/매도 또는 선택 변경 지점
  - 전략이 발동한 기준값
  - 전략이 발동한 날짜

- 복잡한 표는 작은 `table`로 정리
- 차트 가독성을 해치는 과도한 라벨 생성은 피함

- `trend_following` 시각화
  - `tradingPeriod` 이동평균선을 가격 차트에 표시
  - 가격이 이동평균선 위로 올라가 보유 상태가 되는 지점 표시
  - 가격이 이동평균선 아래로 내려가 현금 상태가 되는 지점 표시
  - 진입/청산 표시에는 가격, 이동평균값, `tradingPeriod`를 포함
  - 현재 상태가 `LONG`인지 `CASH`인지 table에 표시

- `dual_momentum` 시각화
  - 리밸런싱 날짜를 차트에 표시
  - 리밸런싱 날짜마다 선택된 자산을 표시
  - 위험자산 1, 위험자산 2, 채권자산의 모멘텀 값을 table에 표시
  - 선택 이유를 `risk asset`, `bond asset`, `cash` 중 하나로 표시
  - 선택 자산이 바뀐 경우 이전 선택과 새 선택을 함께 표시
  - 현재 차트 심볼이 선택 자산과 같아 실제 long 진입이 발생한 지점을 표시

- 기준 표시 원칙
  - 사용자가 차트만 보고도 "언제", "무엇을", "왜" 선택했는지 알 수 있어야 함
  - 신호 표시와 성과 검증을 혼동하지 않도록, Pine Script의 표시는 판단 근거 시각화에 집중

## Logging Rules

- Pine Script는 파일 로그를 만들 수 없음
- 디버깅 정보는 다음 방식으로 대체
  - `plotchar`
  - `plotshape`
  - `label`
  - `table`

- Python 백테스터의 `output/backtest.log`와 동일한 로그를 목표로 하지 않음
- 필요한 판단 근거는 리밸런싱 시점에 차트상에서 확인 가능하게 표시

## Performance Rules

- TradingView 성과는 Strategy Tester를 사용
- Python 백테스터와 동일한 성과표를 Pine Script에서 재현하지 않음
- 추가 투자금, 벤치마크 비교, 연도별 MDD, 파일 리포트는 Python 백테스터 기준으로 유지

## Consistency Rules

- 전략 판단 규칙이 바뀌면 먼저 `backtester/strategy.md` 또는 사용자의 지침을 확인
- Pine Script 제약 때문에 달라지는 내용은 `tradingview/strategy.md`의 `[Pine script 차이점]`에 기록
- 구현 지침이 바뀌면 `tradingview/pine_build.md`를 갱신
- 사용법이 바뀌면 `tradingview/README.md`를 갱신
