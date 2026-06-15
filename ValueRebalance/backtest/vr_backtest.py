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
        
        # 사이클 날짜 계산 (첫 거래일부터 시작)
        cycles = self._generate_cycles(price_data.index[0], price_data.index[-1])
        
        current_cycle_idx = 0
        prev_cycle_close = price_data.iloc[0]['Close']
        
        # 초기 투자: 첫 가격으로 주식 매수 (전액 투자)
        first_price = price_data.iloc[0]['Close']
        if first_price > 0:
            shares = self.config.initial_capital / first_price
        
        # 사이클 데이터 추적용 변수
        cycle_start_data = {
            "v": v_current,
            "pool": pool,
            "evaluation": shares * first_price + pool,
            "shares": shares,
            "date": price_data.index[0]
        }
        cycle_buy_count = 0
        cycle_sell_count = 0
        cycle_traded_shares = 0.0
        
        # 일별 처리
        for date, row in price_data.iterrows():
            close_price = row['Close']
            
            # 현재 평가금 (거래 전)
            evaluation = shares * close_price + pool
            
            # 밴드 계산
            min_band = v_current * (1 - self.config.band_rate)
            max_band = v_current * (1 + self.config.band_rate)
            
            # 거래 신호
            action = None
            traded_shares = 0
            
            if evaluation < min_band and pool > 0:  # 매수
                # 사용 가능한 pool
                usable_pool = pool * self.config.pool_usage_rate
                if usable_pool > 0 and close_price > 0:
                    traded_shares = usable_pool / close_price
                    pool -= usable_pool # 사용 가능한 pool 전체 사용 (traded_shares * close_price 가 정확하지만 수수료 등 고려하면 usable_pool 기준이 맞음)
                    shares += traded_shares
                    action = "buy"
                    self.result.total_trades += 1
                    cycle_buy_count += 1
                    cycle_traded_shares += traded_shares
                
            elif evaluation > max_band and shares > 0:  # 매도
                # 판매할 주식
                sell_shares = shares * self.config.pool_usage_rate
                if sell_shares > 0:
                    sold_value = sell_shares * close_price
                    pool += sold_value
                    shares -= sell_shares
                    action = "sell"
                    self.result.total_trades += 1
                    cycle_sell_count += 1
                    cycle_traded_shares += sell_shares
            
            # 최종 평가금 (거래 후)
            evaluation_after = shares * close_price + pool
            
            # 일일 데이터 저장
            daily = DailyData(
                date=date,
                close_price=close_price,
                evaluation=evaluation_after,
                v_value=v_current,
                pool=pool,
                shares=shares,
                min_band=min_band,
                max_band=max_band,
                action=action,
                traded_shares=traded_shares
            )
            self.result.add_daily_data(daily)
            
            # 사이클 종료 확인
            if current_cycle_idx < len(cycles):
                cycle_end = cycles[current_cycle_idx][1]
                
                if date >= cycle_end or date == price_data.index[-1]:
                    # 사이클 데이터 저장
                    price_change_rate = (close_price - prev_cycle_close) / prev_cycle_close if prev_cycle_close > 0 else 0
                    
                    # 적립금/인출금 적용
                    deposit = 0.0
                    withdrawal = 0.0
                    if self.config.vr_type == "accumulation":
                        deposit = self.config.monthly_amount
                        pool += deposit
                    elif self.config.vr_type == "withdrawal":
                        withdrawal = self.config.monthly_amount
                        pool -= withdrawal
                    
                    # 새 V값 계산
                    v_next = v_current * (1 + price_change_rate / self.config.g) + (deposit - withdrawal)
                    
                    cycle_data = CycleData(
                        cycle_num=current_cycle_idx + 1,
                        start_date=cycle_start_data["date"],
                        end_date=date,
                        v_start=cycle_start_data["v"],
                        pool_start=cycle_start_data["pool"],
                        evaluation_start=cycle_start_data["evaluation"],
                        shares_start=cycle_start_data["shares"],
                        v_end=v_current, # 업데이트 전 V값이 해당 사이클의 V값
                        pool_end=pool,
                        evaluation_end=evaluation_after,
                        shares_end=shares,
                        min_band=min_band,
                        max_band=max_band,
                        price_change_rate=price_change_rate,
                        buy_count=cycle_buy_count,
                        sell_count=cycle_sell_count,
                        total_traded_shares=cycle_traded_shares
                    )
                    self.result.add_cycle_data(cycle_data)
                    
                    # 다음 사이클 준비
                    v_current = v_next
                    prev_cycle_close = close_price
                    current_cycle_idx += 1
                    cycle_start_data = {
                        "v": v_current,
                        "pool": pool,
                        "evaluation": evaluation_after,
                        "shares": shares,
                        "date": date + timedelta(days=1)
                    }
                    cycle_buy_count = 0
                    cycle_sell_count = 0
                    cycle_traded_shares = 0.0
        
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
            # 최신 yfinance는 MultiIndex 컬럼을 반환 → flatten
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
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
    monthly_amount: float = 0.0,
    pool_usage_rate: float = None
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
        pool_usage_rate=pool_usage_rate if pool_usage_rate is not None else vr_config["pool_usage_rate"],
        monthly_amount=monthly_amount,
        start_date=pd.to_datetime(start_date),
        end_date=pd.to_datetime(end_date)
    )
    
    engine = VRBacktestEngine(config)
    return engine.run()
