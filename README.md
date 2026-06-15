# Investment Projects Collection

개인 투자 및 자산 배분을 위한 백테스트 도구와 자동매매 봇 모음입니다.

## 포함된 프로젝트

### 1. ValueRebalance
- **설명**: 포트폴리오의 가치 재조정(Value Rebalancing) 전략을 구현하고 백테스트하는 메인 프로젝트입니다.
- **주요 기능**:
  - VR 전략 백테스트 및 시각화
  - 토스증권 API 연동 (준비 중)
  - 웹 대시보드 (Flask 기반)

### 2. TossBot
- **설명**: 토스증권 Open API를 활용한 자동매매 봇입니다.
- **주요 기능**:
  - 실시간 시세 조회 및 주문 실행
  - 커스텀 전략 적용 가능

### 3. Drip (Dividend Reinvestment Plan)
- **설명**: 배당금 재투자 전략을 자동화하기 위한 도구입니다.
- **주요 기술**: Python, Toss API

### 4. Leverage Backtest
- **설명**: 레버리지 ETF(예: QLD, TQQQ)와 달러 자산을 활용한 투자 전략 백테스트 도구입니다.
- **주요 파일**: `backtest_usd_qld.py`, `dividend_dashboard.html`

### 5. Div-Plan
- **설명**: 배당주 투자 계획 및 비교 도구입니다.
- **주요 기능**: DGRO, DIVO, SCHD 등 주요 배당 ETF 비교 분석

### 6. BackTest2
- **설명**: 나스닥 지수 등을 활용한 추가적인 백테스트 시스템입니다.

---

## 설치 및 실행 방법

각 하위 폴더에는 독립적인 Python 환경(`venv`) 또는 설정 파일이 포함되어 있을 수 있습니다.

1. 의존성 설치:
   ```bash
   pip install -r requirements.txt
   ```
2. 실행 (예시: ValueRebalance):
   ```bash
   cd ValueRebalance
   python app.py
   ```

## 주의사항
- 본 프로젝트에 포함된 API 키 샘플이나 설정 파일은 예시이며, 실제 투자 시에는 본인의 API 키를 안전하게 관리하시기 바랍니다.
- 모든 투자 결정의 책임은 본인에게 있습니다.
