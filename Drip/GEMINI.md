# Drip Project: Python Development Guide

이 프로젝트는 최신 파이썬 패키지 관리 도구인 `uv`를 사용하여 구축되었습니다. `pip`, `venv`, `pyenv` 등을 하나로 대체하며 압도적인 속도를 자랑합니다.

## 🚀 시작하기

### 1. 환경 활성화
`uv`는 `.venv` 디렉토리에 가상환경을 자동으로 관리합니다.
```bash
source .venv/bin/activate
```

### 2. 패키지 추가/삭제
`pip install` 대신 `uv add`를 사용하세요. `pyproject.toml`과 `uv.lock`이 자동으로 업데이트됩니다.
```bash
uv add requests        # 패키지 추가
uv remove requests     # 패키지 삭제
uv add --dev pytest    # 개발용 패키지 추가
```

### 3. 코드 품질 관리 (Ruff)
`ruff`는 Rust로 작성된 초고속 파이썬 린터 및 포맷터입니다.
```bash
uv run ruff check .    # 린팅 체크
uv run ruff format .   # 코드 포맷팅
```

### 4. 테스트 실행
```bash
uv run pytest
```

### 5. 스크립트 실행
가상환경을 수동으로 활성화하지 않아도 `uv run`을 통해 안전하게 실행할 수 있습니다.
```bash
uv run main.py
```

## 🛠️ 주요 설정
- **Package Manager**: `uv`
- **Linter/Formatter**: `ruff`
- **Test Framework**: `pytest`
- **Python Version**: `pyproject.toml`의 `requires-python` 참고
