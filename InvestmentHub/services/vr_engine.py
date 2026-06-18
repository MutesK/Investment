import math
from datetime import datetime, timedelta

class VREngine:
    @staticmethod
    def calculate_next_v(v_before, pool, g, eval_end, extra):
        """
        V_next = V_before + Pool / G + (E - V_before) / 2 * sqrt(G) + extra
        """
        return v_before + (pool / g) + ((eval_end - v_before) / 2 * math.sqrt(g)) + extra

    @staticmethod
    def get_trading_table(current_shares, pool, current_v, band_ratio, pool_limit, buy_unit=1, sell_unit=1):
        """
        Generates buy and sell points based on VR algorithm.
        """
        # Buy Table
        min_band = current_v * (1 - band_ratio)
        max_buy_pool = pool * pool_limit
        
        buy_table = []
        temp_shares = current_shares
        temp_pool_used = 0
        
        # We need at least 1 share to start
        if temp_shares > 0:
            while True:
                buy_price = min_band / temp_shares
                cost = buy_price * buy_unit
                if temp_pool_used + cost > max_buy_pool:
                    break
                
                temp_shares += buy_unit
                temp_pool_used += cost
                buy_table.append({
                    "type": "BUY",
                    "shares": temp_shares,
                    "price": round(buy_price, 2),
                    "pool_left": round(pool - temp_pool_used, 2)
                })
                if len(buy_table) >= 10: break # Limit results

        # Sell Table
        max_band = current_v * (1 + band_ratio)
        sell_table = []
        temp_shares = current_shares
        temp_pool_added = 0
        
        if temp_shares > 1:
            for _ in range(10): # Limit to 10 points
                if temp_shares <= sell_unit: break
                
                target_shares = temp_shares - sell_unit
                sell_price = max_band / target_shares
                temp_pool_added += sell_price * sell_unit
                
                sell_table.append({
                    "type": "SELL",
                    "shares": target_shares,
                    "price": round(sell_price, 2),
                    "pool_left": round(pool + temp_pool_added, 2)
                })
                temp_shares = target_shares

        return {"buy": buy_table, "sell": sell_table}
