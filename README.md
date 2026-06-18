# Investment Projects Collection

개인 투자 및 자산 관리를 위한 통합 플랫폼과 백테스트 도구, 자동매매 봇 모음입니다.

## 포함된 프로젝트

### 1. InvestmentHub ⭐ (메인 대시보드)
- **설명**: 자산 관리, 가계부, 투자 포트폴리오 분석을 위한 올인원 웹 대시보드입니다.
- **주요 기능**:
  - 🏦 **자산 현황 대시보드**: 뱅크샐러드 엑셀 파일 업로드를 통한 자산/부채/순자산 자동 집계
  - 📊 **투자 포트폴리오**: 보유 종목별 투자 원금, 평가 금액, 수익률 시각화 (도넛 차트)
  - 📈 **총자산 증감 추이**: SPY(S&P 500), KOSPI 벤치마크 대비 내 순자산 증감 비교 그래프
  - 📒 **가계부 관리**: 수입/지출 내역 조회, 카테고리별 분석, 월별 필터, 금액 정렬
  - ✏️ **내역 편집**: 거래 내역 카테고리 변경 및 삭제
  - 🔄 **데이터 동기화**: 뱅크샐러드 엑셀 내보내기 파일 업로드 시 가계부 + 자산 현황 동시 반영
  - 📸 **순자산 스냅샷**: 업로드할 때마다 순자산 이력이 누적 기록되어 정확한 자산 변동 추적
- **기술 스택**: Flask, SQLite, Plotly.js, yfinance, Pandas, TailwindCSS
- **실행**:
  ```bash
  cd InvestmentHub
  uv run app.py
  ```

### 2. ValueRebalance
- **설명**: 포트폴리오의 가치 재조정(Value Rebalancing) 전략을 구현하고 백테스트하는 프로젝트입니다.
- **주요 기능**:
  - VR 전략 백테스트 및 시각화
  - 토스증권 API 연동 (준비 중)
  - 웹 대시보드 (Flask 기반)

### 3. TossBot
- **설명**: 토스증권 Open API를 활용한 자동매매 봇입니다.
- **주요 기능**:
  - 실시간 시세 조회 및 주문 실행
  - 커스텀 전략 적용 가능

### 4. Drip (Dividend Reinvestment Plan)
- **설명**: 배당금 재투자 전략을 자동화하기 위한 도구입니다.
- **주요 기술**: Python, Toss API

### 5. Leverage Backtest
- **설명**: 레버리지 ETF(예: QLD, TQQQ)와 달러 자산을 활용한 투자 전략 백테스트 도구입니다.
- **주요 파일**: `backtest_usd_qld.py`, `dividend_dashboard.html`

### 6. Div-Plan
- **설명**: 배당주 투자 계획 및 비교 도구입니다.
- **주요 기능**: DGRO, DIVO, SCHD 등 주요 배당 ETF 비교 분석

### 7. BackTest2
- **설명**: 나스닥 지수 등을 활용한 추가적인 백테스트 시스템입니다.

### 8. StockAnalyzer
- **설명**: 실시간 주식 데이터 분석 도구입니다.
- **주요 기능**:
  - 티커 자동완성 및 직접 입력 검색
  - 기간별(3M, 6M, 1Y, YTD) Beta, 변동성, MDD 계산
  - Plotly 기반 캔들스틱 차트 시각화
- **실행**: `cd StockAnalyzer && streamlit run app.py`

---

## 설치 및 실행 방법

각 하위 폴더에는 독립적인 Python 환경이 포함되어 있습니다.

### InvestmentHub (추천)
```bash
cd InvestmentHub
uv sync          # 의존성 설치
uv run app.py    # 서버 실행 (http://localhost:5000)
```

### 기타 프로젝트
```bash
pip install -r requirements.txt
python app.py
```

## 주의사항
- 본 프로젝트에 포함된 API 키 샘플이나 설정 파일은 예시이며, 실제 투자 시에는 본인의 API 키를 안전하게 관리하시기 바랍니다.
- 모든 투자 결정의 책임은 본인에게 있습니다.
