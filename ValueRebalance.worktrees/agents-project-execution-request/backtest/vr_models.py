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
    """한 사이클의 데이터"""
    cycle_num: int
    start_date: datetime
    end_date: datetime
    
    # 시작값
    v_previous: float
    pool_start: float
    evaluation_start: float
    
    # 변화값
    price_change_rate: float  # 상승률
    
    # 계산값
    v_current: float
    pool_end: float
    evaluation_end: float
    
    # 거래 정보
    buy_price: float = None
    buy_quantity: float = None
    sell_price: float = None
    sell_quantity: float = None
    
    # 추가 입금/출금
    deposit: float = 0.0
    withdrawal: float = 0.0


@dataclass
class DailyData:
    """일일 데이터"""
    date: datetime
    close_price: float
    evaluation: float
    v_value: float
    pool: float
    min_band: float
    max_band: float
    action: str = None  # buy, sell, None


class VRBacktestResult:
    """백테스트 결과"""
    def __init__(self, config: VRConfig):
        self.config = config
        self.daily_data: List[DailyData] = []
        self.cycle_data: List[CycleData] = []
        
        # 통계
        self.total_return: float = 0.0
        self.annual_return: float = 0.0
        self.max_drawdown: float = 0.0
        self.total_trades: int = 0
        self.win_trades: int = 0
        self.lose_trades: int = 0
        
    def add_daily_data(self, data: DailyData):
        self.daily_data.append(data)
    
    def add_cycle_data(self, data: CycleData):
        self.cycle_data.append(data)
    
    def calculate_statistics(self):
        """통계 계산"""
        if not self.daily_data:
            return
        
        initial = self.config.initial_capital
        final = self.daily_data[-1].evaluation
        
        # 수익률
        self.total_return = (final - initial) / initial
        
        # 일일 수익률
        daily_returns = []
        for i in range(1, len(self.daily_data)):
            ret = (self.daily_data[i].evaluation - self.daily_data[i-1].evaluation) / self.daily_data[i-1].evaluation
            daily_returns.append(ret)
        
        if daily_returns:
            # 연 수익률 (근사)
            days = (self.daily_data[-1].date - self.daily_data[0].date).days
            if days > 0:
                self.annual_return = self.total_return * (365 / days)
            
            # 최대낙폭
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
            "config": self.config.__dict__,
            "total_return": self.total_return,
            "annual_return": self.annual_return,
            "max_drawdown": self.max_drawdown,
            "total_trades": self.total_trades,
            "win_trades": self.win_trades,
            "lose_trades": self.lose_trades,
        }
