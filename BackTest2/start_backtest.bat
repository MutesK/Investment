@echo off
setlocal
title QLD & USD DCA Backtest Runner

echo [1/3] 파이썬 설치 확인 중...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 에러: 파이썬이 설치되어 있지 않습니다. python.org에서 설치 후 다시 시도해주세요.
    pause
    exit /b
)

if not exist "venv_win" (
    echo [2/3] 가상환경 생성 및 라이브러리 설치 중 (최초 1회, 수 분 소요)...
    python -m venv venv_win
    call venv_win\Scripts\activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    echo [2/3] 가상환경 확인 완료.
    call venv_win\Scripts\activate
)

echo [3/3] 백테스트 프로그램 실행 중...
streamlit run app.py

pause
