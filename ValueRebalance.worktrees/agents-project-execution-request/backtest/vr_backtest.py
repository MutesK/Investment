"""
VR(Value Rebalancing) 백테스트 엔진
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple
import yfinance as yf

from backtest.vr_models import VRConfig, CycleData, DailyData, VRBacktestResult


class VRBacktestEngine:
    """VR 백테스트 엔진"""
    
    def __init__(self, config: VRConfig):
        self.config = config
        self.result = VRBacktestResult(config)
        
    def run(self) -> VRBacktestResult:
        """백테스트 실행"""
        # 데이터 다운로드
        price_data = self._fetch_price_data()
        
        if price_data is None or len(price_data) == 0:
            raise ValueError("가격 데이터를 가져올 수 없습니다.")
        
        # 초기값 설정
        v_current = self.config.initial_capital
        pool = 0.0
        shares = 0.0
        
        # 사이클 날짜 계산
        cycles = self._generate_cycles(price_data.index[0], price_data.index[-1])
        
        current_cycle_idx = 0
        prev_price = price_data.iloc[0]['Close']
        
        # 일별 처리
        for date, row in price_data.iterrows():
            close_price = float(row['Close'])
            
            # 현재 평가금
            evaluation = float(shares * close_price + pool)
            
            # 밴드 계산
            min_band = float(v_current * (1 - self.config.band_rate))
            max_band = float(v_current * (1 + self.config.band_rate))
            
            # 거래 신호
            action = None
            traded_shares = 0
            
            if evaluation < min_band and pool > 0:  # 매수
                # 사용 가능한 pool
                usable_pool = pool * self.config.pool_usage_rate
                if usable_pool > 0 and close_price > 0:
                    traded_shares = usable_pool / close_price
                    pool -= traded_shares * close_price
                    shares += traded_shares
                    action = "buy"
                    self.result.total_trades += 1
                
            elif evaluation > max_band and shares > 0:  # 매도
                # 판매할 주식
                sell_shares = shares * self.config.pool_usage_rate
                if sell_shares > 0:
                    pool += sell_shares * close_price
                    shares -= sell_shares
                    action = "sell"
                    self.result.total_trades += 1
            
            # 일일 데이터 저장
            daily = DailyData(
                date=date,
                close_price=close_price,
                evaluation=evaluation,
                v_value=v_current,
                pool=pool,
                min_band=min_band,
                max_band=max_band,
                action=action
            )
            self.result.add_daily_data(daily)
            
            # 사이클 종료 확인
            if current_cycle_idx < len(cycles) - 1:
                cycle_end = cycles[current_cycle_idx][1]
                
                if date >= cycle_end:
                    # 새 V값 계산
                    price_change_rate = (close_price - prev_price) / prev_price if prev_price > 0 else 0
                    
                    # 적립금/인출금 적용
                    if self.config.vr_type == "accumulation":
                        monthly_adj = self.config.monthly_amount
                        pool += monthly_adj
                    elif self.config.vr_type == "withdrawal":
                        monthly_adj = -self.config.monthly_amount
                        pool += monthly_adj
                    else:
                        monthly_adj = 0.0
                    
                    v_current = v_current * (1 + price_change_rate / self.config.g) + monthly_adj
                    
                    prev_price = close_price
                    current_cycle_idx += 1
        
        # 통계 계산
        self.result.calculate_statistics()
        
        return self.result
    
    def _fetch_price_data(self) -> pd.DataFrame:
        """yfinance에서 가격 데이터 다운로드"""
        try:
            data = yf.download(
                "TQQQ",
                start=self.config.start_date,
                end=self.config.end_date,
                progress=False
            )
            return data
        except Exception as e:
            print(f"데이터 다운로드 오류: {e}")
            return None
    
    def _generate_cycles(self, start_date: datetime, end_date: datetime) -> List[Tuple[datetime, datetime]]:
        """사이클 날짜 생성 (2주 단위)"""
        cycles = []
        current = start_date
        cycle_days = 14
        
        while current < end_date:
            cycle_end = min(current + timedelta(days=cycle_days), end_date)
            cycles.append((current, cycle_end))
            current = cycle_end + timedelta(days=1)
        
        return cycles


def run_backtest(
    vr_type: str,
    initial_capital: float,
    start_date: str,
    end_date: str,
    band_rate: float = 0.15,
    monthly_amount: float = 0.0
) -> VRBacktestResult:
    """백테스트 실행 함수"""
    
    from config import DEFAULT_VR_CONFIG
    
    vr_config = DEFAULT_VR_CONFIG.get(vr_type)
    if not vr_config:
        raise ValueError(f"지원하지 않는 VR 타입: {vr_type}")
    
    config = VRConfig(
        vr_type=vr_type,
        initial_capital=initial_capital,
        g=vr_config["g"],
        band_rate=band_rate,
        pool_usage_rate=vr_config["pool_usage_rate"],
        monthly_amount=monthly_amount,
        start_date=pd.to_datetime(start_date),
        end_date=pd.to_datetime(end_date)
    )
    
    engine = VRBacktestEngine(config)
    return engine.run()
