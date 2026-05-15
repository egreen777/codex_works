---
name: system-status
description: system_status.py를 실행해 CPU, 메모리, 디스크 사용률을 수집하고 요약한다. 사용자가 시스템 진단, 머신 상태, 리소스 사용률을 요청할 때 사용한다.
---

# 시스템 상태

## 실행 방법
- `scripts/system_status.py`를 Python으로 실행한다.
- stdout의 JSON 문자열을 파싱한다.

## 출력 형식
- JSON 키:
  - `cpu`: CPU 사용률(%)
  - `memory`: 메모리 사용률(%)
  - `storage`: 디스크 사용률(%) (루트 파일시스템)
- JSON을 읽은 뒤 핵심 지표를 자연어로 요약한다.

## 스크립트 위치
- `scripts/system_status.py`
