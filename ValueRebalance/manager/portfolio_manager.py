import json
import os
from datetime import datetime, timedelta
import yfinance as yf
from typing import Dict, List, Optional

class PortfolioManager:
    """실전 투자 포트폴리오 관리자 (라오어 VR 공식 적용)"""
    
    def __init__(self, data_path: str = "data/portfolio.json"):
        self.data_path = data_path
        self.data = self._load_data()
        
    def _load_data(self) -> Dict:
        if os.path.exists(self.data_path):
            with open(self.data_path, "r", encoding="utf-8") as f:
                return json.load(f)
        # 기본 데이터 (사용자 엑셀 기반 초기화)
        return {
            "total_capital": 121737.47,
            "assets": {
                "TIGER 미국나스닥100레버리지": {
                    "ticker": "423920.KS",
                    "currency": "KRW",
                    "settings": { "g": 10, "band_rate": 0.15, "pool_usage_rate": 0.25, "monthly_amount": 250 },
                    "state": {
                        "v_value": 81016.04,
                        "pool": 32949.47,
                        "shares": 1050.0,
                        "start_date": "2026-06-01",
                        "cycle_num": 134,
                        "min_band": 68863.63,
                        "max_band": 93168.45
                    },
                    "history": []
                }
            },
            "last_updated": datetime.now().isoformat()
        }
        
    def save_data(self):
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def get_order_guide(self, name: str) -> Dict:
        """매수/매도 LOC 2중 가이드 계산"""
        asset = self.data["assets"].get(name)
        if not asset: return {}
        
        state = asset["state"]
        settings = asset["settings"]
        
        try:
            stock = yf.Ticker(asset["ticker"])
            current_price = stock.fast_info['last_price']
        except:
            current_price = 0
            
        if current_price <= 0:
            return {"error": "주가 로드 실패"}

        # 1. 매수 LOC 가이드 (평가금이 하단 밴드 밑으로 갈 때)
        # 공식: (MinBand - Pool) / 현재가 -> 이만큼이 주식 가치가 되어야 함
        # 하지만 라오어 방식은 Pool의 일정 비율을 사용하는 것
        buy_usable_pool = state["pool"] * settings["pool_usage_rate"]
        buy_qty = int(buy_usable_pool / current_price) if current_price > 0 else 0
        
        # 2. 매도 LOC 가이드 (평가금이 상단 밴드 위로 갈 때)
        sell_shares_limit = state["shares"] * settings["pool_usage_rate"]
        sell_qty = int(sell_shares_limit)

        return {
            "name": name,
            "current_price": current_price,
            "evaluation": state["shares"] * current_price + state["pool"],
            "v_value": state["v_value"],
            "min_band": state["min_band"],
            "max_band": state["max_band"],
            "buy_guide": {
                "action": "BUY LOC",
                "quantity": buy_qty,
                "target_price": current_price,
                "description": f"평가금이 ₩{state['min_band']:,.0f} 이하로 떨어질 경우 체결"
            },
            "sell_guide": {
                "action": "SELL LOC",
                "quantity": sell_qty,
                "target_price": current_price,
                "description": f"평가금이 ₩{state['max_band']:,.0f} 이상으로 올라갈 경우 체결"
            }
        }

    def update_asset_state(self, name: str, shares: float, pool: float, v_value: float):
        """자산 상태 수동 업데이트 (매매 후 기록용)"""
        if name in self.data["assets"]:
            asset = self.data["assets"][name]
            asset["state"]["shares"] = shares
            asset["state"]["pool"] = pool
            asset["state"]["v_value"] = v_value
            # 밴드 재계산
            asset["state"]["min_band"] = v_value * (1 - asset["settings"]["band_rate"])
            asset["state"]["max_band"] = v_value * (1 + asset["settings"]["band_rate"])
            self.save_data()

    def update_asset_settings(self, name: str, vr_type: str, g: float, band_rate: float, pool_usage_rate: float, monthly_amount: float):
        """전략 설정 업데이트"""
        if name in self.data["assets"]:
            asset = self.data["assets"][name]
            asset["settings"].update({
                "vr_type": vr_type,
                "g": g,
                "band_rate": band_rate,
                "pool_usage_rate": pool_usage_rate,
                "monthly_amount": monthly_amount
            })
            # 설정 변경에 따른 밴드 재계산
            asset["state"]["min_band"] = asset["state"]["v_value"] * (1 - band_rate)
            asset["state"]["max_band"] = asset["state"]["v_value"] * (1 + band_rate)
            self.save_data()
