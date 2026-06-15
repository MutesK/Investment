@echo off
setlocal enabledelayedexpansion

echo ==================================================
echo   TossInvest Trading Bot Windows Setup
echo ==================================================

:: 1. 파이썬 설치 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 파이썬이 설치되어 있지 않거나 PATH에 등록되지 않았습니다.
    echo python.org에서 파이썬을 설치하고 'Add Python to PATH'를 체크해 주세요.
    pause
    exit /b
)

:: 2. 가상환경 생성
if not exist ".venv" (
    echo [1/3] 가상환경(.venv)을 생성합니다...
    python -m venv .venv
) else (
    echo [1/3] 이미 가상환경이 존재합니다.
)

:: 3. 필수 패키지 설치
echo [2/3] 필수 라이브러리를 설치합니다...
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install yfinance pandas numpy playwright

:: 4. Playwright 브라우저 설치
echo [3/3] 브라우저 엔진을 설치합니다...
python -m playwright install chromium

echo ==================================================
echo   설치가 완료되었습니다!
echo   실행 방법: call .venv\Scripts\activate ^&^& python trading_bot.py
echo ==================================================
pause
