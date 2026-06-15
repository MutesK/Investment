"""
백테스트용 브로커 구현
"""
from broker.base_broker import BacktestBroker


class VRBacktestBroker(BacktestBroker):
    """VR 백테스트용 전문화된 브로커"""
    
    def __init__(self, initial_balance: float = 100000):
        super().__init__(initial_balance)
        self.trades = []
    
    def record_trade(self, date, ticker: str, order_type: str, quantity: float, price: float):
        """거래 기록"""
        self.trades.append({
            "date": date,
            "ticker": ticker,
            "type": order_type,
            "quantity": quantity,
            "price": price,
            "value": quantity * price
        })
    
    def get_trade_history(self):
        """거래 히스토리 조회"""
        return self.trades
