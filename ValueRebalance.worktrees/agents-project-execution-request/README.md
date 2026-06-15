# ValueRebalance

TQQQ 밸류 리벨런싱(Value Rebalancing) 백테스트 시스템

## 개요

이 프로젝트는 적립식, 거치식, 인출식 VR(Value Rebalancing) 전략을 백테스트하고 시각화하는 시스템입니다.

### VR의 3가지 운용 방식
- **적립식 VR**: 주기적으로 일정한 금액을 적립 (공격적)
- **거치식 VR**: 추가 적립/인출 없이 장기 투자 (중립)
- **인출식 VR**: 주기적으로 일정 금액을 인출 (안정적)

## 주요 기능

✅ 웹 기반 시나리오 설정 (기간, 초기 자금, 파라미터)
✅ TQQQ 역사 데이터를 이용한 백테스트 (yfinance)
✅ 실시간 인터랙티브 그래프 시각화 (Plotly)
✅ 매매 신호 표시 (매수/매도)
✅ 일별 상세 데이터 추적
✅ 향후 증권사 API 연동 지원 (토스증권 등)

## 프로젝트 구조

```
ValueRebalance/
├── backtest/
│   ├── __init__.py
│   ├── vr_backtest.py          # 핵심 백테스트 엔진
│   ├── vr_models.py            # V, Pool, G 등 데이터 모델
│   └── visualizer.py           # 그래프 시각화 (Plotly)
├── broker/
│   ├── __init__.py
│   ├── base_broker.py          # 증권사 API 추상화 인터페이스
│   ├── backtest_broker.py      # 백테스트용 브로커
│   └── toasecurities.py        # 토스증권 연동 (향후)
├── templates/
│   └── index.html              # 웹 UI (반응형 디자인)
├── app.py                       # Flask 웹 애플리케이션
├── config.py                    # 설정 파일
├── requirements.txt             # 의존성
└── README.md                    # 이 파일
```

## 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/MutesK/ValueRebalance.git
cd ValueRebalance
```

### 2. 가상 환경 설정
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 웹 서버 실행
```bash
python app.py
```

### 5. 웹 브라우저에서 접속
```
http://localhost:5000
```

## 사용 방법

### 웹 UI 설명

**좌측 사이드바:**
- 추천 시나리오 버튼 (1년, 3년, 5년)
- VR 방식 선택 (적립식/거치식/인출식)
- 초기 자금 설정
- 백테스트 기간 선택
- 밴드 설정 (±10%, ±15%, ±20%)
- 월별 적립/인출금

**백테스트 실행:**
1. 좌측에서 파라미터 설정
2. "백테스트 실행" 버튼 클릭
3. 로딩 완료 후 결과 확인

### 그래프 해석

**1번 그래프 (상단):**
- 🔴 빨간색 선: 현재 평가금 (보유 주식 가치 + 캐시)
- 🟢 초록색 점선: 최소/최대 밴드 (±밴드%)
- 🟠 주황색 실선: V값 (목표 가이드 가격)
- 🔼 초록 삼각형: 매수 신호
- 🔽 빨간 삼각형: 매도 신호

**2번 그래프 (하단):**
- 🔵 파란색 선: Pool 변동 (현금 저장소)

### 요약 통계

- **초기 자금**: 설정한 초기 투자 금액
- **최종 평가금**: 백테스트 종료 시 총 자산
- **총 수익률**: (최종 - 초기) / 초기 × 100%
- **연 수익률**: 연율화된 수익률
- **최대낙폭**: 과거 최고점 대비 최대 하락률
- **총 거래**: 매수/매도 총 횟수
- **최종 Pool**: 백테스트 종료 시 남은 현금
- **최종 보유 주식**: 백테스트 종료 시 보유한 TQQQ 주식 수

## VR 파라미터 설명

### G (Gradient) - 기울기

새로운 V값 계산 공식:
```
V₂ = V₁ × (1 + 상승률/G) ± 적립금
```

- G값이 클수록 안정적 (변화 완만)
- G값이 작을수록 공격적 (변화 가파름)
- 기본값: 적립식/거치식 G=10, 인출식 G=20

### 밴드 (Band) - 매매 구간

- 평가금이 V값의 (1 - 밴드%) 아래 → 매수
- 평가금이 V값의 (1 + 밴드%) 위 → 매도
- 권장: ±10%, ±15%, ±20%

### Pool 사용 한도

각 VR 방식의 기본값:
- **적립식**: Pool의 75% (공격적)
- **거치식**: Pool의 50% (중립)
- **인출식**: Pool의 25% (보수적)

한도를 낮출수록 더 안정적이지만 투자 효율이 감소합니다.

## 향후 개발 계획

- [ ] 토스증권 Open API 연동
- [ ] 실시간 자동매매
- [ ] 더 많은 종목 지원 (QQQ, SPY 등)
- [ ] 포트폴리오 최적화
- [ ] 성과 비교 분석
- [ ] 데이터 내보내기 (CSV, Excel)
- [ ] 알림 설정
- [ ] 모바일 앱

## 기술 스택

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Data**: yfinance, pandas, numpy
- **Visualization**: Plotly
- **UI/UX**: Responsive Design

## 면책 조항

⚠️ 이 소프트웨어는 교육 목적으로만 제공됩니다. 실제 투자 결정에 대한 책임은 사용자에게 있습니다.

## 라이센스

MIT License

## 연락처

이슈 및 피드백: https://github.com/MutesK/ValueRebalance/issues
