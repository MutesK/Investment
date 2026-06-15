"""
증권사 API 추상화 인터페이스
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, List


class BaseBroker(ABC):
    """증권사 API 기본 인터페이스"""
    
    @abstractmethod
    def authenticate(self, credentials: Dict) -> bool:
        """인증"""
        pass
    
    @abstractmethod
    def get_balance(self) -> Dict:
        """잔액 조회"""
        pass
    
    @abstractmethod
    def get_holdings(self) -> List[Dict]:
        """보유 종목 조회"""
        pass
    
    @abstractmethod
    def get_stock_price(self, ticker: str) -> float:
        """종목 가격 조회"""
        pass
    
    @abstractmethod
    def buy_order(self, ticker: str, quantity: float, price: Optional[float] = None) -> str:
        """매수 주문"""
        pass
    
    @abstractmethod
    def sell_order(self, ticker: str, quantity: float, price: Optional[float] = None) -> str:
        """매도 주문"""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """주문 취소"""
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> Dict:
        """주문 상태 조회"""
        pass
    
    @abstractmethod
    def set_reserve_order(self, ticker: str, order_type: str, quantity: float, price: float, date: datetime) -> str:
        """예약 주문 설정"""
        pass


class BacktestBroker(BaseBroker):
    """백테스트용 브로커 (에뮬레이션)"""
    
    def __init__(self, initial_balance: float = 100000):
        self.balance = initial_balance
        self.holdings = {}
        self.orders = {}
        self.order_counter = 0
    
    def authenticate(self, credentials: Dict) -> bool:
        """에뮬레이션용 인증 (항상 성공)"""
        return True
    
    def get_balance(self) -> Dict:
        """잔액 조회"""
        return {"cash": self.balance}
    
    def get_holdings(self) -> List[Dict]:
        """보유 종목 조회"""
        result = []
        for ticker, quantity in self.holdings.items():
            result.append({"ticker": ticker, "quantity": quantity})
        return result
    
    def get_stock_price(self, ticker: str) -> float:
        """종목 가격 조회 (외부 소스 필요)"""
        raise NotImplementedError("외부 데이터 소스 필요")
    
    def buy_order(self, ticker: str, quantity: float, price: float) -> str:
        """매수 주문"""
        cost = quantity * price
        if cost > self.balance:
            raise ValueError("잔액 부족")
        
        self.balance -= cost
        self.holdings[ticker] = self.holdings.get(ticker, 0) + quantity
        
        self.order_counter += 1
        order_id = f"BUY_{self.order_counter}"
        self.orders[order_id] = {
            "type": "buy",
            "ticker": ticker,
            "quantity": quantity,
            "price": price,
            "status": "filled"
        }
        return order_id
    
    def sell_order(self, ticker: str, quantity: float, price: float) -> str:
        """매도 주문"""
        if self.holdings.get(ticker, 0) < quantity:
            raise ValueError("보유 수량 부족")
        
        self.balance += quantity * price
        self.holdings[ticker] -= quantity
        
        self.order_counter += 1
        order_id = f"SELL_{self.order_counter}"
        self.orders[order_id] = {
            "type": "sell",
            "ticker": ticker,
            "quantity": quantity,
            "price": price,
            "status": "filled"
        }
        return order_id
    
    def cancel_order(self, order_id: str) -> bool:
        """주문 취소"""
        if order_id in self.orders:
            self.orders[order_id]["status"] = "cancelled"
            return True
        return False
    
    def get_order_status(self, order_id: str) -> Dict:
        """주문 상태 조회"""
        return self.orders.get(order_id, {})
    
    def set_reserve_order(self, ticker: str, order_type: str, quantity: float, price: float, date: datetime) -> str:
        """예약 주문 설정"""
        self.order_counter += 1
        order_id = f"RESERVE_{self.order_counter}"
        self.orders[order_id] = {
            "type": order_type,
            "ticker": ticker,
            "quantity": quantity,
            "price": price,
            "date": date,
            "status": "pending"
        }
        return order_id
