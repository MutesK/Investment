#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== TossInvest Trading Bot 환경 설정 시작 ===${NC}"

# 1. 가상환경 생성 (.venv)
if [ ! -d ".venv" ]; then
    echo -e "${GREEN}[1/4] 가상환경(.venv)을 생성합니다...${NC}"
    python3 -m venv .venv
else
    echo -e "${BLUE}[1/4] 이미 가상환경이 존재합니다.${NC}"
fi

# 2. 가상환경 활성화
echo -e "${GREEN}[2/4] 가상환경을 활성화합니다...${NC}"
source .venv/bin/activate

# 3. 필수 패키지 설치
echo -e "${GREEN}[3/4] 필수 라이브러리를 설치합니다 (yfinance, pandas, numpy)...${NC}"
pip install --upgrade pip
pip install yfinance pandas numpy playwright

# 4. tossctl 호환성을 위한 Playwright 브라우저 설치 (선택 사항이지만 권장)
echo -e "${GREEN}[4/4] Playwright 브라우저 엔진을 설치합니다...${NC}"
python3 -m playwright install chromium

echo -e "${BLUE}=== 모든 설정이 완료되었습니다! ===${NC}"
echo -e "다음 명령어로 프로그램을 실행하세요:"
echo -e "${GREEN}source .venv/bin/activate && python trading_bot.py${NC}"
