# InvestmentHub Project Progress Report

## 프로젝트 개요
여러 흩어져 있던 투자 관련 도구(Backtesting, Stock Analysis, Value Rebalancing, Dividend Planning)를 하나로 통합한 Flask 기반 웹 플랫폼입니다.

## 현재 상태 (Status: 2026-06-18)
- **프레임워크:** Flask + Tailwind CSS (Dark Mode)
- **패키지 관리:** `uv`
- **데이터베이스:** SQLite (SQLAlchemy) - `InvestmentHub/instance/investment_hub.db`

## 완료된 작업 (Done)
1. **Foundation (The Shell):**
   - 통합 대시보드 및 사이드바 내비게이션 구축.
   - 다크 모드 UI 일관성 적용.
   - 순환 참조(Circular Import) 문제 해결을 위한 `database.py` 분리.

2. **Market Analyzer 모듈:**
   - 티커별 캔들차트 및 MDD 그래프 구현 (Plotly.js).
   - Beta, Volatility, MDD 주요 지표 계산 로직 이식.

3. **Backtesting 모듈 (전면 개편):**
   - **Portfolio Builder UI:** 사용자가 여러 티커를 추가하여 포트폴리오를 구성하는 방식.
   - **DCA 시뮬레이션:** 초기 거치금 및 월 적립금을 반영한 정확한 자산 성장 시뮬레이션.
   - **그래프 개선:** 선형 출력 문제를 해결하고 실시간 변동성을 반영하도록 보정.
   - **데이터 로딩:** `yfinance` MultiIndex 및 환율(`USDKRW=X`) 데이터 정렬 이슈 해결.

4. **Value Rebalancing (VR) 모듈:**
   - `Asset.py` 기반의 핵심 VR 알고리즘(V계산, 매수/매도 밴드) 이식.
   - 자산 추가/수정/삭제(CRUD) 기능 구현.
   - **사이클 관리:** "Finish Cycle & Start Next" 버튼을 통한 자동 V값 갱신 기능.
   - 실시간 주가 기반 Order Guide(매수/매도 포인트) 출력.

5. **Dividend Planner 모듈:**
   - 실시간 배당률(Yield) 및 3년 연평균 배당 성장률(CAGR) 계산 로직 정교화.
   - `yfinance` API 응답 형식 차이에 따른 수치 오류 수정.

## 다음 작업 (Next Steps / Pending)
1. **Trading Bot 통합:** `TossBot` 및 `Drip` 로직을 이식하여 실제 주문 체결 상태 확인 기능 추가 필요.
2. **데이터 캐싱:** `yfinance` API 호출 최적화를 위한 서버 사이드 캐싱 로직 강화.
3. **사용자 설정:** DB에 API 키나 개인 설정을 저장할 수 있는 프로필/설정 페이지.
4. **리포트 익스포트:** 백테스트 결과를 PDF나 Excel로 저장하는 기능.

## 실행 방법
```bash
cd InvestmentHub
uv run python app.py
```
서버 주소: `http://127.0.0.1:5001`

---
*이 문서는 추후 작업 재개 시 참고용으로 작성되었습니다.*
