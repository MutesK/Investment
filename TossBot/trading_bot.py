import sys
import logging
from toss_client import TossClient
from strategy import TradingEngine

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("TossTradingBot")

def main():
    """메인 실행 함수"""
    # 1. 클라이언트 및 엔진 초기화
    client = TossClient()
    engine = TradingEngine(client=client)

    # 2. 실행 인자가 있으면 티커 등록
    # (실행 인자는 첫 등록 용도로만 사용)
    input_args = sys.argv[1:]
    if input_args:
        logger.info(f"📥 새로운 티커 등록을 시도합니다: {input_args}")
        engine.register_tickers(input_args)

    # 3. 엔진 가동 (무한 루프 내부에서 상태 출력 및 자동 매매 수행)
    try:
        engine.run()
    except Exception as e:
        logger.critical(f"💥 엔진이 치명적인 에러로 중단되었습니다: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
