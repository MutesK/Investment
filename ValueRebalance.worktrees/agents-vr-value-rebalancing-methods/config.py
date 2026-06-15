"""
ValueRebalance 설정 파일
"""

# Flask 설정
DEBUG = True
HOST = "0.0.0.0"
PORT = 5000

# VR 기본 파라미터
DEFAULT_VR_CONFIG = {
    "accumulation": {  # 적립식
        "name": "적립식",
        "g": 10,
        "pool_usage_rate": 0.75,
        "description": "주기적 적립, 공격적 운용"
    },
    "holding": {  # 거치식
        "name": "거치식",
        "g": 10,
        "pool_usage_rate": 0.50,
        "description": "추가 적립/인출 없음, 중립"
    },
    "withdrawal": {  # 인출식
        "name": "인출식",
        "g": 20,
        "pool_usage_rate": 0.25,
        "description": "주기적 인출, 안정적 운용"
    }
}

# 권장 밴드 설정
RECOMMENDED_BANDS = [0.10, 0.15, 0.20]  # ±10%, ±15%, ±20%

# 백테스트 설정
BACKTEST_CONFIG = {
    "ticker": "TQQQ",
    "cycle_days": 14,  # 2주 사이클
    "min_pool_usage_rate": 0.10,  # 최소 10% (권장하지 않음)
    "min_capital": 1000,  # 최소 투자 금액
    "max_capital": 10000000,  # 최대 투자 금액
}

# 시간대 설정
TIMEZONE = "Asia/Seoul"

# 데이터 캐시 설정
CACHE_EXPIRY_HOURS = 24
