"""
VR(Value Rebalancing) 데이터 모델
"""
from dataclasses import dataclass
from typing import List
from datetime import datetime


@dataclass
class VRConfig:
    """VR 설정"""
    vr_type: str  # accumulation, holding, withdrawal
    initial_capital: float
    g: float  # Gradient (기울기)
    band_rate: float  # 밴드 비율 (0.10, 0.15, 0.20)
    pool_usage_rate: float  # Pool 사용 한도
    monthly_amount: float = 0.0  # 적립금 or 인출금 (월별)
    start_date: datetime = None
    end_date: datetime = None


@dataclass
class CycleData:
    """한 사이클의 데이터 (2주 단위)"""
    cycle_num: int
    start_date: datetime
    end_date: datetime
    
    # 시작값
    v_start: float
    pool_start: float
    evaluation_start: float
    shares_start: float
    
    # 종료값 (V는 사이클 종료 시 업데이트됨)
    v_end: float
    pool_end: float
    evaluation_end: float
    shares_end: float
    
    # 밴드 정보
    min_band: float
    max_band: float
    
    # 수익률
    price_change_rate: float
    
    # 거래 요약
    buy_count: int = 0
    sell_count: int = 0
    total_traded_shares: float = 0.0


@dataclass
class DailyData:
    """일일 데이터"""
    date: datetime
    close_price: float
    evaluation: float
    v_value: float
    pool: float
    shares: float
    min_band: float
    max_band: float
    action: str = None  # buy, sell, None
    traded_shares: float = 0.0


class VRBacktestResult:
    """백테스트 결과"""
    def __init__(self, config: VRConfig):
        self.config = config
        self.daily_data: List[DailyData] = []
        self.cycle_data: List[CycleData] = []
        
        # 요약 통계
        self.initial_evaluation: float = 0.0
        self.final_evaluation: float = 0.0
        self.total_return: float = 0.0
        self.annual_return: float = 0.0
        self.max_drawdown: float = 0.0
        self.total_trades: int = 0
        self.final_pool: float = 0.0
        self.final_shares: float = 0.0
        
    def add_daily_data(self, data: DailyData):
        self.daily_data.append(data)
    
    def add_cycle_data(self, data: CycleData):
        self.cycle_data.append(data)
    
    def calculate_statistics(self):
        """통계 계산"""
        if not self.daily_data:
            return
        
        self.initial_evaluation = self.config.initial_capital
        self.final_evaluation = self.daily_data[-1].evaluation
        self.final_pool = self.daily_data[-1].pool
        self.final_shares = self.daily_data[-1].shares
        
        # 수익률
        self.total_return = (self.final_evaluation - self.initial_evaluation) / self.initial_evaluation
        
        # 연 수익률
        days = (self.daily_data[-1].date - self.daily_data[0].date).days
        if days > 0:
            self.annual_return = ((1 + self.total_return) ** (365 / days)) - 1
        
        # 최대낙폭 (MDD)
        peak = self.daily_data[0].evaluation
        max_dd = 0.0
        for data in self.daily_data:
            if data.evaluation > peak:
                peak = data.evaluation
            dd = (peak - data.evaluation) / peak
            if dd > max_dd:
                max_dd = dd
        self.max_drawdown = max_dd

    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            "config": {
                "vr_type": self.config.vr_type,
                "initial_capital": self.config.initial_capital,
                "g": self.config.g,
                "band_rate": self.config.band_rate,
                "pool_usage_rate": self.config.pool_usage_rate,
                "monthly_amount": self.config.monthly_amount,
                "start_date": self.config.start_date.strftime("%Y-%m-%d"),
                "end_date": self.config.end_date.strftime("%Y-%m-%d")
            },
            "summary": {
                "initial_evaluation": self.initial_evaluation,
                "final_evaluation": self.final_evaluation,
                "total_return": self.total_return,
                "annual_return": self.annual_return,
                "max_drawdown": self.max_drawdown,
                "total_trades": self.total_trades,
                "final_pool": self.final_pool,
                "final_shares": self.final_shares
            }
        }
