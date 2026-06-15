# 🚀 TossInvest 2-Sigma Trading Bot

이 프로젝트는 토스 증권의 비공식 CLI 도구인 `tossctl`을 활용하여, 미국/한국 주식의 **2시그마 하락 지점**에서 자동으로 매수 주문을 예약하는 트레이딩 봇입니다.

---

## 💻 윈도우(Windows) 설치 가이드

### 1. 필수 프로그램 설치
1.  **Python**: [python.org](https://www.python.org/)에서 최신 버전을 다운로드하여 설치하세요. **반드시 'Add Python to PATH' 옵션을 체크**해야 합니다.
2.  **tossctl**: [tossinvest-cli 리리즈 페이지](https://github.com/JungHoonGhae/tossinvest-cli/releases)에서 `windows_amd64.zip`을 다운로드하고 압축을 푼 뒤, `tossctl.exe` 파일을 적당한 폴더에 넣고 그 폴더를 시스템 환경 변수의 **PATH**에 추가하세요.

### 2. 로그인 및 설정 (PowerShell에서 실행)
```powershell
# 1. 로그인
tossctl auth login

# 2. 설정 초기화
tossctl config init

# 3. 모든 트레이딩 옵션 허용 (아래 코드를 한 줄로 복사해서 실행)
python -c "import json, os; p=os.path.join(os.environ['APPDATA'], 'tossctl', 'config.json'); d=json.load(open(p)); d['trading']={'place':True,'sell':True,'kr':True,'fractional':True,'cancel':True,'amend':True,'allow_live_order_actions':True,'dangerous_automation':{'accept_fx_consent':True}}; json.dump(d, open(p, 'w'), indent=2)"

# 4. 트레이딩 권한 승인 (휴대폰 토스 앱에서 승인 버튼 클릭 필수)
tossctl order permissions grant --ttl 3600
```

### 3. 봇 실행
1.  `setup.bat` 파일을 더블 클릭하여 라이브러리를 설치합니다.
2.  설치가 끝나면 터미널에서 아래 명령어로 봇을 실행합니다.
    ```powershell
    .venv\Scripts\activate
    python trading_bot.py USD QLD 005930
    ```

---

## 🍎 맥(macOS) 설치 가이드

### 1. 필수 프로그램 설치
```bash
# Homebrew 및 필수 도구 설치
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python nodejs git

# tossctl 설치
curl -fsSL https://raw.githubusercontent.com/JungHoonGhae/tossinvest-cli/main/install.sh | sh
```

### 2. 로그인 및 설정
```bash
# 1. 로그인 및 권한 승인
tossctl auth login
tossctl config init

# 2. 모든 트레이딩 옵션 허용
python3 -c 'import json; p="/Users/$(whoami)/Library/Application Support/tossctl/config.json"; d=json.load(open(p)); d["trading"]={"place":True,"sell":True,"kr":True,"fractional":True,"cancel":True,"amend":True,"allow_live_order_actions":True,"dangerous_automation":{"accept_fx_consent":True}}; json.dump(d, open(p, "w"), indent=2)'

# 3. 권한 승인 (휴대폰 확인!)
tossctl order permissions grant --ttl 3600
```

### 3. 봇 실행
```bash
chmod +x setup.sh
./setup.sh
source .venv/bin/activate
python trading_bot.py USD QLD 005930
```

---

## ⚙️ 공통 설정 및 사용 팁

### 주요 업데이트 사항
- **기본 종목 변경**: 기존 3배수(TQQQ, SOXL)에서 2배수(USD, QLD)로 기본 설정이 변경되었습니다.
- **세션 체크 기능**: 시작 시 및 주문 전 토스증권 세션이 살아있는지 자동으로 확인합니다.
- **주문 중복 방지**: 봇에 의해 이미 주문이 들어간 종목은 당일 중복 주문하지 않습니다. (개인적인 수동 주문은 무시하고 봇의 전략대로 주문을 넣습니다.)

### 종목 지정 실행
명령어 뒤에 원하는 종목(티커 또는 한국 종목코드)을 나열하면 됩니다.
```bash
python trading_bot.py USD QLD NVDA 005930 000660
```

### 스케줄러 시간 변경
`trading_bot.py` 파일 하단의 `target_time="18:00"`을 원하는 시간으로 수정하세요. (한국 시간 기준)

### 알파(α) 값 조정
`SigmaStrategyBot(alpha=0.01)`의 숫자를 조정하여 매수 지점을 조절할 수 있습니다.
- `0.01`: 2시그마 지점보다 1% 위에서 매수 (체결 확률 높음)
- `0.00`: 정확히 2시그마 지점에서 매수
- `-0.01`: 2시그마 지점보다 1% 더 아래에서 매수 (더 싸게 사기)

---

## ⚠️ 주의사항 (Disclaimer)
- 본 프로그램은 개인적인 투자 보조 도구입니다.
- 실제 주문이 발생하는 프로그램이므로 반드시 `DRY_RUN` 테스트(tossctl 설정 활용)를 거친 후 사용하세요.
- 비공식 API를 사용하므로 서비스 환경에 따라 예고 없이 작동이 중단될 수 있습니다.
