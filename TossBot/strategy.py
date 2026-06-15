import json
import os
import datetime
import logging
import time
import yfinance as yf
import threading
import sys
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import pytz

from toss_client import TossClient

logger = logging.getLogger("TossTradingBot.Strategy")

class BaseStrategy(ABC):
    """모든 매수 전략의 기반이 되는 추상 클래스"""
    def __init__(self, client: TossClient):
        self.client = client

    def _get_market_info(self, symbol: str):
        if symbol.endswith(".KS") or symbol.endswith(".KQ"):
            return "kr", symbol
        if len(symbol) == 6:
            return "kr", f"{symbol}.KS"
        return "us", symbol

    def _round_price(self, price: float, market: str, symbol: str) -> float:
        if market == "us":
            return round(price, 2)
        price = int(price)
        is_kr_etf = len(symbol) == 6 and (symbol.isdigit() or any(c.isalpha() for c in symbol))
        if is_kr_etf:
            tick = 5 if price < 100000 else 10
        else:
            if price < 2000: tick = 1
            elif price < 5000: tick = 5
            elif price < 10000: tick = 10
            elif price < 50000: tick = 50
            elif price < 100000: tick = 100
            elif price < 500000: tick = 500
            else: tick = 1000
        return (price // tick) * tick

    def execute_buy_order(
        self,
        symbol: str,
        price: float,
        quantity: float = 0,
        amount: float = 0,
        is_fractional: bool = False,
    ):
        market, _ = self._get_market_info(symbol)
        if market == "kr" and not is_fractional:
            quantity = int(quantity)

        adjusted_price = self._round_price(price, market, symbol)
        preview = self.client.preview_order(
            symbol, "buy", adjusted_price, quantity, market=market, 
            is_fractional=is_fractional, amount=amount
        )
        
        if "confirm_token" not in preview:
            logger.error(f"❌ {symbol} 프리뷰 실패: {preview.get('message', preview)}")
            return preview

        token = preview["confirm_token"]
        order_desc = f"{quantity}주" if not is_fractional else f"{int(amount)}원"
        logger.info(f"🚀 [ORDER] {symbol} ({market.upper()}) {order_desc} 매수 명령 전송... (기준가: {adjusted_price})")
        
        result = self.client.place_order(
            token, symbol, "buy", adjusted_price, quantity, market=market, 
            is_fractional=is_fractional, amount=amount
        )

        if result.get("error") or "error" in str(result).lower():
            msg = result.get("message", "Unknown error")
            if "400" in str(result) and market == "kr":
                logger.error(f"❌ 잘못된 요청 (400): 한국 시장 거래 시간(09:00~15:30)인지 확인하세요.")
            logger.warning(f"⚠️ 결과: {msg}")
        else:
            logger.info(f"✅ 완료: {result}")
        return result

    @abstractmethod
    def run(self, symbol_targets: Dict[str, Any]):
        pass

class SigmaStrategy(BaseStrategy):
    """2시그마 하락가 기반 매수 전략"""
    def __init__(self, client: TossClient, alpha: float = 0.01):
        super().__init__(client)
        self.alpha = alpha

    def calculate_historical_sigma(self, symbol: str) -> float:
        market, yf_ticker = self._get_market_info(symbol)
        logger.info(f"📊 {symbol} 시그마 계산 중...")
        ticker = yf.Ticker(yf_ticker)
        hist = ticker.history(period="max")
        if hist.empty and market == "kr" and yf_ticker.endswith(".KS"):
            yf_ticker = yf_ticker.replace(".KS", ".KQ")
            ticker = yf.Ticker(yf_ticker)
            hist = ticker.history(period="max")
        if hist.empty:
            logger.error(f"Failed to fetch data for {symbol}")
            return 0.0
        returns = hist["Close"].pct_change().dropna()
        return returns.std()

    def run(self, symbol_targets: Dict[str, Any]):
        symbols = list(symbol_targets.keys())
        quotes = self.client.quote_batch(symbols)
        quote_map = {q["symbol"]: q for q in quotes if isinstance(q, dict) and "symbol" in q}

        for symbol, target_val in symbol_targets.items():
            market, _ = self._get_market_info(symbol)
            is_fractional = False
            quantity, amount = 0.0, 0.0
            
            if isinstance(target_val, str) and target_val.startswith("f"):
                is_fractional, amount = True, float(target_val[1:])
            else:
                try: quantity = float(target_val)
                except ValueError: continue

            sigma = self.calculate_historical_sigma(symbol)
            if sigma == 0: continue

            prev_close, current_price = 0, 0
            if symbol in quote_map:
                prev_close = quote_map[symbol].get("reference_price", 0)
                current_price = quote_map[symbol].get("last", 0)

            if prev_close == 0:
                _, yf_ticker = self._get_market_info(symbol)
                ticker = yf.Ticker(yf_ticker)
                hist = ticker.history(period="5d")
                if not hist.empty:
                    prev_close = hist["Close"].iloc[-1]
                    current_price = prev_close
                else: continue

            target_price = prev_close * (1 - 2 * sigma + self.alpha)
            display_target = f"${target_price:.2f}" if market == "us" else f"{int(target_price)}원"
            display_current = f"${current_price:.2f}" if market == "us" else f"{int(current_price)}원"
            
            if market == "us" and is_fractional:
                # 미국 주식 소수점: 장 시작 시 즉시 시장가 매수
                logger.info(f"🔍 {symbol} 분석: 미국 소수점 매수 설정됨. 즉시 매수를 진행합니다.")
                self.execute_buy_order(symbol=symbol, price=current_price, amount=amount, is_fractional=True)
            else:
                # 한국 주식 전체 및 미국 주식 온주: 2시그마 하락가 지정가 예약
                if market == "kr" and is_fractional:
                    logger.warning(f"⚠️ {symbol}: 한국 주식은 소수점 매수가 불가능합니다. 일반 지정가 주문으로 전환합니다.")
                
                logger.info(f"🔍 {symbol} 분석: 현재가={display_current}, 목표가={display_target}")
                self.execute_buy_order(symbol=symbol, price=target_price, quantity=quantity, is_fractional=False)


class TradingEngine:
    """자동 매매 및 배당 재투자 통합 엔진"""
    def __init__(self, client: TossClient, state_file: str = "bot_state.json"):
        self.client = client
        self.state_file = state_file
        self.state = self._load_state()
        self.tz_kst = pytz.timezone("Asia/Seoul")
        self.stop_event = threading.Event()

    def _load_state(self) -> Dict[str, Any]:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    state = json.load(f)
                    if "registered_tickers" not in state: state["registered_tickers"] = {}
                    if "processed_dividend_ids" not in state: state["processed_dividend_ids"] = []
                    if "last_run" not in state: state["last_run"] = {}
                    return state
            except Exception as e:
                logger.warning(f"⚠️ 상태 파일을 불러오지 못했습니다: {e}")
        return {
            "registered_tickers": {}, 
            "processed_dividend_ids": [],
            "last_run": {},
            "orders": []
        }

    def _save_state(self):
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"❌ 상태 저장 실패: {e}")

    def register_tickers(self, input_args: List[str]):
        """입력 인자를 분석하여 티커 등록"""
        if not input_args: return

        for arg in input_args:
            if ":" in arg:
                parts = arg.split(":")
                symbol = parts[0].upper()
                target = parts[1]
                strategy_name = parts[2] if len(parts) > 2 else "sigma"
            else:
                symbol = arg.upper()
                target = "1"
                strategy_name = "sigma"
            
            self.state["registered_tickers"][symbol] = {
                "target": target,
                "strategy": strategy_name,
                "added_at": datetime.datetime.now().isoformat()
            }
            logger.info(f"📌 티커 등록 완료: {symbol} (전략: {strategy_name}, 목표: {target})")
        
        self._save_state()

    def list_tickers(self):
        """현재 등록된 티커 목록 출력"""
        tickers = self.state.get("registered_tickers", {})
        if not tickers:
            logger.info("ℹ️ 현재 등록된 티커가 없습니다.")
            return
        
        logger.info("📋 [등록된 티커 목록]")
        for sym, info in tickers.items():
            logger.info(f" - {sym}: {info['target']} ({info['strategy']})")

    def remove_ticker(self, symbol: str):
        """티커 삭제"""
        symbol = symbol.upper()
        if symbol in self.state["registered_tickers"]:
            del self.state["registered_tickers"][symbol]
            self._save_state()
            logger.info(f"🗑️ 티커 삭제 완료: {symbol}")
        else:
            logger.warning(f"⚠️ 삭제 실패: {symbol}을 찾을 수 없습니다.")

    def _command_loop(self):
        """사용자 입력을 처리하는 전용 스레드 루프"""
        logger.info("💡 실시간 명령 입력이 가능합니다. (명령어: add, del, list, test, help, exit)")
        while not self.stop_event.is_set():
            try:
                # 입력을 받기 위해 프롬프트 출력
                sys.stdout.write("> ")
                sys.stdout.flush()
                cmd_input = sys.stdin.readline().strip()
                if not cmd_input: continue

                parts = cmd_input.split()
                cmd = parts[0].lower()
                args = parts[1:]

                if cmd == "add" and args:
                    self.register_tickers(args)
                elif cmd == "del" and args:
                    for sym in args: self.remove_ticker(sym)
                elif cmd == "list":
                    self.list_tickers()
                elif cmd == "test":
                    self.test_tickers()
                elif cmd == "help":
                    logger.info("❓ [도움말] add, del, list, test, exit")
                elif cmd == "exit":
                    logger.info("👋 엔진 종료 중...")
                    self.stop_event.set()
                    break
                else:
                    logger.warning(f"⚠️ 알 수 없는 명령입니다: {cmd}")
            except Exception as e:
                logger.error(f"❌ 명령 처리 중 에러: {e}")

    def test_tickers(self):
        """등록된 티커들의 현재가와 목표가를 계산하여 출력 (주문 없음)"""
        tickers = self.state.get("registered_tickers", {})
        if not tickers:
            logger.info("ℹ️ 테스트할 티커가 없습니다.")
            return
        
        logger.info("🔍 [티커 분석 테스트 시작]")
        symbols = list(tickers.keys())
        quotes = self.client.quote_batch(symbols)
        quote_map = {q["symbol"]: q for q in quotes if isinstance(q, dict) and "symbol" in q}
        
        sigma_strat = SigmaStrategy(self.client)
        
        for symbol, info in tickers.items():
            market, _ = sigma_strat._get_market_info(symbol)
            sigma = sigma_strat.calculate_historical_sigma(symbol)
            
            prev_close, current_price = 0, 0
            if symbol in quote_map:
                prev_close = quote_map[symbol].get("reference_price", 0)
                current_price = quote_map[symbol].get("last", 0)
            
            if prev_close > 0:
                target_price = prev_close * (1 - 2 * sigma + sigma_strat.alpha)
                target_price = sigma_strat._round_price(target_price, market, symbol)
                
                disp_curr = f"${current_price:.2f}" if market == "us" else f"{int(current_price)}원"
                disp_targ = f"${target_price:.2f}" if market == "us" else f"{int(target_price)}원"
                
                logger.info(f"📊 {symbol}: 현재가 {disp_curr} / 목표가 {disp_targ} (상태: {'매수권' if current_price <= target_price else '대기'})")
            else:
                logger.warning(f"⚠️ {symbol}: 시세를 가져올 수 없습니다.")
        logger.info("🔍 [티커 분석 테스트 종료]")

    def _get_us_market_open_time(self, now: datetime.datetime):
        """서머타임 고려한 미국 장 시작 시간 반환 (KST 기준)"""
        if 3 <= now.month <= 10:
            return 22, 30
        return 23, 30

    def check_market_opening(self):
        """장 시작 시점에 전략 실행"""
        now = datetime.datetime.now(self.tz_kst)
        today_str = now.strftime("%Y-%m-%d")
        
        if today_str not in self.state["last_run"]:
            self.state["last_run"][today_str] = []

        # 1. 한국 시장 (09:00)
        if now.hour == 9 and now.minute <= 10 and "kr_open" not in self.state["last_run"][today_str]:
            kr_tickers = {s: info["target"] for s, info in self.state["registered_tickers"].items() 
                          if s.endswith((".KS", ".KQ")) or len(s) == 6}
            if kr_tickers:
                logger.info(f"🇰🇷 한국 시장 장 시작! 전략을 실행합니다. (대상: {', '.join(kr_tickers.keys())})")
                SigmaStrategy(self.client).run(kr_tickers)
                self.state["last_run"][today_str].append("kr_open")
                self._save_state()

        # 2. 미국 시장 (22:30 / 23:30)
        us_open_h, us_open_m = self._get_us_market_open_time(now)
        if now.hour == us_open_h and now.minute <= 10 and "us_open" not in self.state["last_run"][today_str]:
            us_tickers = {s: info["target"] for s, info in self.state["registered_tickers"].items() 
                          if not (s.endswith((".KS", ".KQ")) or len(s) == 6)}
            if us_tickers:
                logger.info(f"🇺🇸 미국 시장 장 시작! 전략을 실행합니다. (대상: {', '.join(us_tickers.keys())})")
                SigmaStrategy(self.client).run(us_tickers)
                self.state["last_run"][today_str].append("us_open")
                self._save_state()

    def check_and_reinvest_dividends(self):
        """배당금 확인 및 미국 주식 소수점 재투자 (통화 구분)"""
        now = datetime.datetime.now()
        if not hasattr(self, '_last_div_check') or (now - self._last_div_check).seconds > 3600:
            logger.info("💰 배당금 내역 확인 중...")
            self._last_div_check = now

        for market in ["us", "kr"]:
            ledger = self.client.ledger_transactions(market=market)
            if not isinstance(ledger, list): continue

            for tx in ledger:
                tx_id = tx.get("id") or str(tx)
                if tx_id in self.state["processed_dividend_ids"]: continue
                
                desc = tx.get("description", "") or tx.get("type", "")
                if "배당" in desc or "Dividend" in desc:
                    amount = float(tx.get("amount", 0))
                    currency = tx.get("currency", "USD" if market == "us" else "KRW").upper()
                    if amount <= 0: continue

                    us_symbols = [s for s in self.state["registered_tickers"].keys() 
                                  if not (s.endswith((".KS", ".KQ")) or len(s) == 6)]
                    
                    logger.info(f"✨ 새로운 배당금 발견! ({market.upper()}): {amount} {currency}")
                    logger.info(f"🔄 재투자 대상 미국 주식: {', '.join(us_symbols) if us_symbols else '없음'}")
                    
                    self._process_reinvestment(amount, currency)
                    self.state["processed_dividend_ids"].append(tx_id)
                    self._save_state()

    def _process_reinvestment(self, total_amount: float, currency: str):
        """미국 주식들에 균등 소수점 투자 (통화 반영)"""
        us_symbols = [s for s in self.state["registered_tickers"].keys() 
                      if not (s.endswith((".KS", ".KQ")) or len(s) == 6)]
        
        if not us_symbols:
            logger.warning("⚠️ 재투자할 미국 주식이 등록되어 있지 않습니다.")
            return

        each_amount = total_amount / len(us_symbols)
        
        # 통화별 최소 주문 금액 체크
        min_amount = 0.01 if currency == "USD" else 1000
        if each_amount < min_amount:
            logger.warning(f"⚠️ 배당금이 너무 적어 재투자를 건너뜁니다. (종목당 {each_amount:.2f} {currency})")
            return

        logger.info(f"🔄 총 {len(us_symbols)}개 미국 종목에 각 {each_amount:.2f} {currency}씩 재투자합니다.")
        for symbol in us_symbols:
            quote = self.client.quote_get(symbol)
            current_price = quote.get("last", 0) if isinstance(quote, dict) else 0
            
            preview = self.client.preview_order(
                symbol, "buy", current_price, 0, 
                market="us", is_fractional=True, amount=each_amount, currency_mode=currency
            )
            
            if "confirm_token" in preview:
                self.client.place_order(
                    preview["confirm_token"], symbol, "buy", current_price, 0, 
                    market="us", is_fractional=True, amount=each_amount, currency_mode=currency
                )
                logger.info(f"✅ {symbol} 재투자 주문 완료 ({each_amount:.2f} {currency})")
            else:
                logger.error(f"❌ {symbol} 재투자 프리뷰 실패: {preview.get('message', preview)}")

    def run(self):
        """엔진 메인 루프"""
        logger.info("🏁 매매 엔진이 가동되었습니다. (무한 루프 시작)")
        self.list_tickers()
        
        # 커맨드 처리 스레드 시작
        cmd_thread = threading.Thread(target=self._command_loop, daemon=True)
        cmd_thread.start()
        
        last_status_time = time.time()
        
        while not self.stop_event.is_set():
            try:
                # 1. 세션 체크 및 자동 로그인
                if not self.client.check_session():
                    time.sleep(10)
                    continue

                # 2. 주기적으로 등록된 티커 목록 출력 (1시간마다)
                current_time = time.time()
                if current_time - last_status_time > 3600:
                    self.list_tickers()
                    last_status_time = current_time

                # 3. 장 시작 체크 및 전략 실행
                self.check_market_opening()

                # 4. 배당금 체크
                self.check_and_reinvest_dividends()

                # 5. 대기 (10초 간격으로 단축하여 종료 이벤트에 빠르게 반응)
                for _ in range(6):
                    if self.stop_event.is_set(): break
                    time.sleep(10)
                    
            except KeyboardInterrupt:
                logger.info("🛑 사용자에 의해 엔진이 중단되었습니다.")
                self.stop_event.set()
                break
            except Exception as e:
                logger.error(f"❌ 엔진 루프 중 에러 발생: {e}")
                time.sleep(60)
