import subprocess
import json
import os
import sys
import time
import logging
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger("TossTradingBot.Client")


class TossClient:
    """
    tossinvest-cli (tossctl) 전 기능을 지원하는 종합 래퍼 클래스.
    모든 명령어는 내부적으로 --output json을 사용하여 딕셔너리 형태로 반환합니다.
    """

    def __init__(self):
        self._ensure_config()

    def _get_config_path(self) -> str:
        """OS별 tossctl 설정 파일 경로 반환"""
        if sys.platform == "win32":
            base = os.environ.get("APPDATA", "")
            return os.path.join(base, "tossctl", "config.json")
        else:
            return os.path.expanduser(
                "~/Library/Application Support/tossctl/config.json"
            )

    def _ensure_config(self):
        """거래 권한 플래그 자동 활성화"""
        config_path = self._get_config_path()
        if not os.path.exists(config_path):
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            changed = False
            if "trading" not in config:
                config["trading"] = {}
                changed = True

            t = config["trading"]
            keys_to_enable = [
                "place",
                "sell",
                "kr",
                "fractional",
                "cancel",
                "amend",
                "allow_live_order_actions",
            ]

            for key in keys_to_enable:
                if t.get(key) is not True:
                    t[key] = True
                    changed = True

            if "dangerous_automation" not in t:
                t["dangerous_automation"] = {}
                changed = True

            if t["dangerous_automation"].get("accept_fx_consent") is not True:
                t["dangerous_automation"]["accept_fx_consent"] = True
                changed = True

            if changed:
                logger.info("⚙️ tossctl 거래 권한 설정을 자동으로 활성화했습니다.")
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"❌ 설정 파일 업데이트 실패: {e}")

    def call(
        self, subcommands: List[str], flags: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        임의의 tossctl 명령어를 실행합니다.

        Args:
            subcommands: ['account', 'summary']와 같은 명령 계층
            flags: {'--symbol': 'AAPL', '--qty': 1}와 같은 플래그 딕셔너리
        """
        cmd = ["tossctl"] + subcommands + ["--output", "json"]

        if flags:
            for key, value in flags.items():
                if value is True:
                    cmd.append(key)
                elif value is False or value is None:
                    continue
                else:
                    cmd.append(key)
                    cmd.append(str(value))

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if not result.stdout.strip():
                return {}
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            try:
                # 에러 메시지도 JSON인 경우 파싱
                return json.loads(e.stderr)
            except:
                return {"error": True, "message": e.stderr.strip() or str(e)}
        except json.JSONDecodeError:
            return {"error": True, "message": "JSON Parse Error", "raw": result.stdout}

    def _run_interactive(self, args: list):
        """인터랙티브 명령 실행 (QR 코드 출력 등을 위해 stdout을 캡처하지 않음)"""
        cmd = ["tossctl"] + args
        try:
            # shell=False가 기본이며, 출력을 캡처하지 않아 터미널에 바로 표시됨
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    # --- Auth & Session ---
    def check_session(self) -> bool:
        """세션 유효성 체크 및 자동 권한 승인. 만료 시 자동 로그인 시도."""
        status = self.call(["auth", "status"])

        # 세션이 유효한 경우
        if isinstance(status, dict) and status.get("valid") is True:
            logger.info("✅ 토스증권 세션이 유효합니다.")
            self.order_permissions_grant()
            return True

        # 세션이 유효하지 않은 경우 자동 로그인 시도
        logger.warning(
            "⚠️ 세션이 만료되었습니다. 자동으로 헤드리스 로그인을 시작합니다..."
        )
        if self.auth_login_headless():
            logger.info("원격 로그인이 완료되었습니다. 세션을 다시 확인합니다.")
            # 로그인 후 다시 한 번 상태 확인
            status = self.call(["auth", "status"])
            if isinstance(status, dict) and status.get("valid") is True:
                logger.info("✅ 로그인 성공! 세션이 활성화되었습니다.")
                self.order_permissions_grant()
                return True

        logger.error(
            "❌ 로그인에 실패했습니다. 'tossctl auth login'을 수동으로 실행해 주세요."
        )
        return False

    def auth_login(self):
        """로그인 명령어 실행 (인터랙티브 브라우저 팝업)"""
        return self._run_interactive(["auth", "login"])

    def auth_login_headless(self, qr_path: Optional[str] = "/tmp/toss-qr.png"):
        """
        헤드리스 로그인 실행 (콘솔 QR 코드 인증)
        """
        args = ["auth", "login", "--headless"]
        if qr_path:
            args.extend(["--qr-output", qr_path])

        logger.info("🔑 아래 QR 코드를 토스 앱으로 스캔하여 로그인해 주세요.")
        return self._run_interactive(args)

    # --- Account & Portfolio ---
    def account_list(self):
        return self.call(["account", "list"])

    def account_summary(self):
        return self.call(["account", "summary"])

    def portfolio_positions(self):
        return self.call(["portfolio", "positions"])

    def portfolio_allocation(self):
        return self.call(["portfolio", "allocation"])

    # --- Quotes & Watchlist ---
    def quote_get(self, symbol: str):
        return self.call(["quote", "get", symbol])

    def quote_batch(self, symbols: List[str]):
        return self.call(["quote", "batch"] + symbols)

    def watchlist_list(self):
        return self.call(["watchlist", "list"])

    # --- Orders Management ---
    def orders_list(self):
        """미체결 주문 목록"""
        return self.call(["orders", "list"])

    def orders_completed(self, market: str = "all"):
        """체결 완료 주문 내역 (market: us, kr, all)"""
        return self.call(["orders", "completed"], {"--market": market})

    def order_show(self, order_id: str):
        """특정 주문 상세 정보"""
        return self.call(["order", "show", order_id])

    # --- Trading ---
    def order_permissions_grant(self, ttl: int = 3600):
        """거래 권한 승인 (Grant)"""
        logger.info(f"🔑 거래 권한 승인 시도 (TTL: {ttl}s)...")
        res = self.call(["order", "permissions", "grant"], {"--ttl": ttl})
        if isinstance(res, dict) and res.get("error"):
            logger.warning(f"⚠️ 권한 승인 알림: {res.get('message')}")
        return res

    def order_permissions_status(self):
        return self.call(["order", "permissions", "status"])

    def preview_order(
        self,
        symbol: str,
        side: str,
        price: float,
        quantity: float,
        market: str = "us",
        is_fractional: bool = False,
        amount: float = 0,
        currency_mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        """주문 프리뷰"""
        if not currency_mode:
            currency_mode = "USD" if market == "us" else "KRW"

        flags = {
            "--symbol": symbol,
            "--side": side,
            "--market": market,
            "--currency-mode": currency_mode,
        }

        if is_fractional:
            flags.update(
                {
                    "--type": "market",
                    "--fractional": True,
                    "--amount": int(amount),
                    "--qty": 0,
                }
            )
        else:
            flags.update(
                {
                    "--type": "limit",
                    "--price": f"{price:.2f}" if market == "us" else int(price),
                    "--qty": quantity,
                }
            )

        return self.call(["order", "preview"], flags)

    def place_order(
        self,
        confirm_token: str,
        symbol: str,
        side: str,
        price: float,
        quantity: float,
        market: str = "us",
        is_fractional: bool = False,
        amount: float = 0,
        currency_mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        """주문 실행"""
        if not currency_mode:
            currency_mode = "USD" if market == "us" else "KRW"

        flags = {
            "--confirm": confirm_token,
            "--symbol": symbol,
            "--side": side,
            "--market": market,
            "--currency-mode": currency_mode,
            "--execute": True,
            "--dangerously-skip-permissions": True,
        }

        if is_fractional:
            flags.update(
                {
                    "--type": "market",
                    "--fractional": True,
                    "--amount": int(amount),
                    "--qty": 0,
                }
            )
        else:
            flags.update(
                {
                    "--type": "limit",
                    "--price": f"{price:.2f}" if market == "us" else int(price),
                    "--qty": quantity,
                }
            )

        return self.call(["order", "place"], flags)

    def order_cancel(self, order_id: str, symbol: str):
        """주문 취소"""
        return self.call(
            ["order", "cancel"], {"--order-id": order_id, "--symbol": symbol}
        )

    # --- Transactions & Ledger ---
    def ledger_transactions(self, market: str = "us"):
        """거래 내역 리스트"""
        return self.call(["ledger", "transactions", "list"], {"--market": market})

    def transactions_overview(self, market: str = "us"):
        """잔고/예수금 개요"""
        return self.call(["overview", "transactions", "overview"], {"--market": market})

    # --- Push ---
    def push_listen(self):
        """
        실시간 푸시 리스너 실행 (JSONL 스트림 출력)
        직접 호출보다는 별도 프로세스나 스레드에서 관리하는 것이 좋습니다.
        """
        cmd = ["tossctl", "push", "listen", "--output", "json"]
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
