# Build And Execution Guide

이 문서는 `invest_backtest.md`를 기반으로 백테스터 구현 시 따라야 하는 개발 지침을 정리한다.  
목적은 다른 agent나 model이 작업하더라도 동일한 동작과 결과를 유지하도록 하는 것이다.

## Scope

- 대상 시장: 미국 ETF
- 데이터 주기: 일봉
- 용도: 전략 검증용 백테스트
- 차트: 첫 버전 제외
- 세금/수수료: 첫 버전 제외

## Project Structure

- `backtester/code`
  - 실행 코드
- `backtester/data`
  - 다운로드한 CSV 데이터
- `backtester/output`
  - 리포트 및 로그 출력
- `backtester/strategy.md`
  - 투자 전략 상세 정의
- `backtester/build.md`
  - 구현 지침

## Data Rules

- 가격 데이터 소스
  - Yahoo Finance 사용

- 저장 형식
  - CSV
  - 컬럼: `Date, Open, High, Low, Close, Adj Close, Volume`

- 저장 위치
  - `backtester/data/{ticker}.csv`

- 로딩 방식
  - 해당 티커 CSV가 있고 요청 기간을 모두 포함하면 재다운로드하지 않음
  - 부족한 경우에만 추가 다운로드 후 병합

- 선행 데이터 확보 규칙
  - 실제 백테스트 시작일보다 최소 1년 앞선 날짜부터 데이터를 확보
  - 이유: `trading-period`가 최대 200일 수준이므로 시작일 직후에도 판단이 가능해야 함

- 실제 성과 계산 시작일
  - 사용자가 입력한 `--start`부터
  - 그 이전 데이터는 지표 계산을 위한 워밍업 용도

- 데이터 부족 허용 규칙
  - 상장일이 늦어서 과거 데이터가 부족할 수 있음
  - 이 경우 현재처럼 `trading-period`가 충분하지 않은 상태를 허용하고, 가능한 시점부터 전략이 동작하게 둘 것

- 가격 기준
  - 계산은 `Adj Close` 기준

## CLI Rules

- 공통 파라미터
  - `--strategy`
  - `--start`
  - `--end`
  - `--initial-capital`
  - `--annual-contribution`
  - `--trading-period`
  - `--rebalancing-period`
  - `--save-report`

- 기본값
  - `--trading-period 120`
  - `--rebalancing-period 3m`

- 전략별 사용 규칙
  - `trend_following`
    - 사용: `--ticker`, `--trading-period`
    - 미사용: `--tickers`, `--bond-ticker`, `--rebalancing-period`
  - `dual_momentum`
    - 사용: `--tickers`, `--bond-ticker`, `--trading-period`, `--rebalancing-period`
  - `asset_allocation`
    - 사용: `--tickers`, `--bond-ticker`, `--trading-period`, `--rebalancing-period`

- 무시 파라미터 처리
  - 선택한 전략과 맞지 않는 파라미터는 에러로 막지 않고 무시 가능
  - 단, 사용자에게 `parameter was ignored` 메시지를 출력
  - 예외: 전략에 필수인 인자가 없으면 즉시 종료

- 다중 자산 입력 형식
  - `--tickers QQQ:40,VOO:25`
  - `--bond-ticker IEF`
  - 비중 미입력 시 남는 비중을 미지정 자산에 균등 배분

## Strategy Execution Rules

- 추세추종
  - 오늘 종가로 신호 계산
  - 다음 거래일부터 포지션 반영

- 듀얼 모멘텀
  - 리밸런싱 시점마다 `trading-period` 수익률 계산
  - 2개 위험자산 중 더 강한 자산을 찾음
  - 그 자산이 채권보다 강하면 위험자산 보유
  - 위험자산이 둘 다 채권보다 약하면 채권 보유
  - 위험자산과 채권이 모두 음수면 현금 보유

- 자산배분
  - 목표 비중 유지
  - 리밸런싱 시점마다 목표 비중으로 복원

- 리밸런싱 시점
  - `1m`, `3m`, `6m`, `9m`, `1y`
  - 각 기간의 마지막 거래일
  - 휴일이면 직전 마지막 거래일

## Performance Rules

- 연도별 표
  - `year`
  - `end_value`
  - `return`
  - `mdd`
  - `BM value`
  - `BM return`
  - `BM mdd`

- 최종 표
  - `period`
  - `ending_value`
  - `cumulative_return`
  - `CAGR`
  - `overall_MDD`
  - `average_holding_days`
  - `total_principal`

- 벤치마크 규칙
  - 단일 종목 전략: 해당 종목 `buy and hold`
  - 다중 자산 전략: `VOO buy and hold`

- 추가 투자금 반영
  - 매년 1월 1일이 아니라 해당 연도의 첫 거래일에 반영

- `average_holding_days`
  - 현재 구현은 평균 자산 교체 기간이 아니라, 포지션이 비어 있지 않은 연속 구간의 평균 거래일 수

## Report Rules

- 타이틀
  - 고정 문자열: `MY BACKTESTING REPORT`

- 포함 정보
  - 전략명
  - 전략 상세 설명
  - 사용 자산
  - 벤치마크
  - 룰 코드
  - `trading-period`
  - 필요 시 `rebalancing-period`
  - 초기 투자금
  - 연간 추가 투자금
  - 무시된 파라미터 메시지
  - 연도별 성과표
  - 최종 성과표

- 정렬 규칙
  - 콘솔에서 표 칸이 어긋나지 않도록 공백 정렬 유지

## Logging Rules

- 로그 파일
  - `backtester/output/backtest.log`

- 기록 방식
  - append 방식
  - 실행마다 새 블록 추가

- 기록 내용
  - 실행 시각
  - 전략명
  - 요청 기간
  - 사용 자산
  - 벤치마크
  - `trading-period`
  - `rebalancing-period`
  - 초기 투자금
  - 연간 추가 투자금
  - 최종 수익 요약
  - 무시된 파라미터
  - 전략 이벤트

- 이벤트 기록 규칙
  - 추세추종
    - 진입/이탈 시점
    - 가격
    - `trading-period`
    - 해당 시점 누적수익률
  - 듀얼 모멘텀
    - 리밸런싱 날짜
    - `selected_before -> selected_after`
    - 의사결정 종류
    - `trading-period`
    - `rebalancing-period`
    - 해당 시점 누적수익률
    - 자산별 모멘텀 값
  - 자산배분
    - 리밸런싱 날짜
    - 목표 비중
    - `trading-period`
    - `rebalancing-period`
    - 해당 시점 누적수익률

## Consistency Rules

- `invest_backtest.md`
  - 사용자가 만든 작업 가이드
  - 요구사항 원문으로 유지

- `strategy.md`
  - 투자 전략의 상세 규칙만 관리

- `build.md`
  - 구현 방식, 데이터 규칙, CLI 규칙, 출력 규칙, 로그 규칙을 통합 관리

- 향후 수정 원칙
  - 전략 정의가 바뀌면 먼저 `strategy.md` 갱신
  - 구현 방식이 바뀌면 `build.md` 갱신
  - 사용자 요구 자체가 바뀌면 `invest_backtest.md` 갱신
