
from enum import Enum
from dataclasses import dataclass, field
import math
from datetime import datetime, timedelta, date


class VRType(Enum) : 
    ACUMULATION = 1 
    DEFERRAL = 2
    WITHDRAWAL = 3


PoolLimit = 0.75
BandRatio = 0.15
G = 10

class BandType(Enum) :
    BUY = 0
    SELL = 1

@dataclass
class TradingTable :
    Type: BandType = BandType.BUY
    AssetCount: int = 0
    TradingPoint: float = 0.0
    PoolStat: int = 0

# 사이클 정보
    # 1. 사이클 카운트 및 사이클 기간 ( 2주 )
    # 2. 시작 평가금
    # 3. 사이클 마지막 평가금
    # 4. V값
    # 5. 최소밴드, 최대밴드
    # 6. 시작 Pool, 사이클 마지막 Pool
@dataclass
class Cycle :
    start_time: str = ""
    end_time : str = ""
    cycle_count : int = 0
    eval_start : int = 0
    eval_end : int = 0
    current_v : int = 0
    mininum_band : int = 0
    maximum_band : int = 0
    pool_start : int = 0
    pool_end : int = 0
    buy_trading_tables : list[TradingTable] = field(default_factory=list)
    sell_trading_tables : list[TradingTable] = field(default_factory=list)




class Calculator:
    # 다음 사이클의 V값을 계산합니다.
    # Pool = 예수금
    # G = 기울기
    # E = 직전사이클 마지막 평가금
    # extra = 적립금 or 인출금
    @staticmethod
    def CalculateV (V_before : int, Pool : int, 
    G : float, E: int, extra : int) :
        return V_before + Pool / G + (E - V_before) / 2 * math.sqrt(G) + extra


# 밸류리벨런싱 특성상 처음에는 무조건 한주는 가지고 잇어야 알고리즘이 작동함.
# 사이클은 월요일 기준으로 2주 사용. 
# 0번째 사이클의 기간은 무시한다.
class Asset :
    def __init__(self, code: str, name: str, count : int,
                     eval : int, P: int, extra : int, start_date: str = None,
                     buy_unit: int = 1, sell_unit: int = 1 ):
        self.ticker = code
        self.name = name
        self.count = count
        self.type = VRType.ACUMULATION
        self.buy_unit = buy_unit
        self.sell_unit = sell_unit

        if self.type == VRType.DEFERRAL :
            self.extra = 0
        else:
            self.extra = extra

        self.cycles = []
        
        # Determine starting Monday date
        if start_date is None:
            today_dt = date.today()
            start_dt = today_dt - timedelta(days=today_dt.weekday())
        else:
            if isinstance(start_date, str):
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            else:
                start_dt = start_date
            start_dt = start_dt - timedelta(days=start_dt.weekday())

        cycle1 = Cycle()
        cycle1.cycle_count = 1
        cycle1.start_time = start_dt.strftime("%Y-%m-%d")
        cycle1.end_time = (start_dt + timedelta(weeks=2)).strftime("%Y-%m-%d")
        cycle1.eval_start = eval
        cycle1.current_v = eval
        cycle1.mininum_band = eval * (1 - BandRatio)
        cycle1.maximum_band = eval * (1 + BandRatio)
        cycle1.pool_start = P
        cycle1.pool_end = 0
        cycle1.buy_trading_tables = self.CalculrateBuyTable(cycle1)
        cycle1.sell_trading_tables = self.CalculrateSellTable(cycle1)

        self.cycles.append(cycle1)


    def ChangeType(self, type : VRType, extra : int) : 
        self.type = type

        if self.type == VRType.DEFERRAL :
            self.extra = 0
        else:
            self.extra = extra
        

    # 사이클을 계산한다. 주기에 맞게 실행해야함.
    def CalculrateCycle(self, eval_end : int = 0) :
        before_cycle = self.cycles[-1]
        new_cycle = Cycle()

        before_cycle.eval_end = eval_end  # 사이클이 끝났을때 해당 자산의 평가액

        new_cycle.cycle_count = before_cycle.cycle_count + 1
        new_cycle.eval_start = before_cycle.eval_end
        
        # Calculate new cycle dates (2 weeks, Monday-based)
        if before_cycle.end_time:
            start_dt = datetime.strptime(before_cycle.end_time, "%Y-%m-%d").date()
            new_cycle.start_time = before_cycle.end_time
            new_cycle.end_time = (start_dt + timedelta(weeks=2)).strftime("%Y-%m-%d")
        else:
            new_cycle.start_time = ""
            new_cycle.end_time = ""

        new_cycle.current_v = Calculator.CalculateV(before_cycle.current_v, before_cycle.pool_end,
            G, before_cycle.eval_end, self.extra)
        new_cycle.mininum_band = new_cycle.current_v * (1 - BandRatio)
        new_cycle.maximum_band = new_cycle.current_v * (1 + BandRatio)
        new_cycle.pool_start = before_cycle.pool_end + self.extra
        new_cycle.buy_trading_tables = self.CalculrateBuyTable(new_cycle)
        new_cycle.sell_trading_tables = self.CalculrateSellTable(new_cycle)

        self.cycles.append(new_cycle)

    def CalculrateBuyTable(self, cycle : Cycle) : 
        mininum_band = cycle.mininum_band
        count = self.count # 보유 개수
        pool = cycle.pool_start # 보유 예수금
        max_usage = pool * PoolLimit # 최대 가능 매수금액
        usage = 0

        buy_trading_tables : list[TradingTable] = []

        if count <= 0 or mininum_band <= 0 or max_usage <= 0:
            return buy_trading_tables

        while True:
            trading_point = mininum_band / count
            next_cost = trading_point * self.buy_unit
            if usage + next_cost > max_usage:
                break
            new_table = TradingTable()
            new_table.Type = BandType.BUY
            new_table.AssetCount = count + self.buy_unit
            new_table.TradingPoint = trading_point
            usage += next_cost
            new_table.PoolStat = int(pool - usage)
            count = count + self.buy_unit
            buy_trading_tables.append(new_table)

        return buy_trading_tables

    def CalculrateSellTable(self, cycle : Cycle) : 
        maximum_band = cycle.maximum_band
        count = self.count
        pool = cycle.pool_start
        
        sell_trading_tables : list[TradingTable] = []

        if count <= 1 or maximum_band <= 0:
            return sell_trading_tables

        received_cash = 0
        for i in range(self.sell_unit, count, self.sell_unit) :
            new_table = TradingTable()
            new_table.Type = BandType.SELL
            new_table.AssetCount = count - i
            new_table.TradingPoint = maximum_band / (count - i)
            transaction_income = self.sell_unit * new_table.TradingPoint
            received_cash += transaction_income
            new_table.PoolStat = int(pool + received_cash)
            sell_trading_tables.append(new_table)

        return sell_trading_tables



            


            

    
        


            
            

        

    

    
