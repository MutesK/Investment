"""
VR 백테스트 엑셀 핸들러
입력 템플릿 생성 및 결과 내보내기 기능
"""
import pandas as pd
from datetime import datetime
from backtest.vr_models import VRBacktestResult, VRConfig


def generate_template(file_path: str):
    """사용자 친화적인 입문용 입력 템플릿 생성"""
    data = {
        "설정 항목": [
            "1. VR 운용 방식",
            "2. 초기 투자 자금 ($)",
            "3. 백테스트 시작일",
            "4. 백테스트 종료일",
            "5. 매매 밴드 (±%)",
            "6. 월 적립/인출금 ($)",
            "7. 현금(Pool) 사용 한도"
        ],
        "입력값": [
            "accumulation",
            10000,
            "2023-01-01",
            datetime.now().strftime("%Y-%m-%d"),
            0.15,
            500,
            0.75
        ],
        "설명 및 허용 범위": [
            "accumulation(적립식), holding(거치식), withdrawal(인출식) 중 입력",
            "처음 주식을 매수할 총 자금 (최소 1000$ 권장)",
            "YYYY-MM-DD 형식 (예: 2021-01-01)",
            "YYYY-MM-DD 형식 또는 오늘 날짜",
            "0.1(10%) ~ 0.2(20%) 사이 권장 (소수로 입력)",
            "매달 추가로 넣거나 뺄 금액 (거치식은 0 입력)",
            "매매 시 보유 현금의 몇 %를 사용할지 (0.1 ~ 0.9 사이 소수 입력)"
        ]
    }
    df = pd.DataFrame(data)
    
    # 엑셀 파일 생성 및 서식 적용
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="VR_입력설정")
        sheet = writer.sheets["VR_입력설정"]
        # 컬럼 너비 조정
        sheet.column_dimensions['A'].width = 25
        sheet.column_dimensions['B'].width = 20
        sheet.column_dimensions['C'].width = 50


def parse_input(file_path: str) -> dict:
    """엑셀 파일에서 파라미터 파싱 (기본 템플릿 및 자추 VR 양식 지원)"""
    xls = pd.ExcelFile(file_path)
    
    # 1. 'VR' 시트가 있는지 확인 (자추 VR 양식)
    if 'VR' in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name='VR')
        
        # 데이터가 시작되는 행 찾기 (헤더 'No' 다음 행)
        start_row = 0
        for i, row in df.iterrows():
            if row.iloc[1] == 1: # 'No' 컬럼이 1인 행
                start_row = i
                break
        
        first_data = df.iloc[start_row]
        
        # 자추 양식에서 파라미터 추출
        # Unnamed: 4 (시작일), Unnamed: 7 (초기V), Unnamed: 13 (적립금), Unnamed: 16 (사용한도)
        # 밴드는 VR MIN(8) / VR TARGET(7) 비율로 추정
        initial_v = float(first_data.iloc[7])
        min_v = float(first_data.iloc[8])
        band_rate = round(1 - (min_v / initial_v), 2)
        
        # 마지막 데이터 행 찾기 (종료 날짜용)
        last_row_idx = df.iloc[start_row:].dropna(subset=[df.columns[4]]).index[-1]
        last_data = df.loc[last_row_idx]
        
        params = {
            "vr_type": "accumulation", # 기본적으로 적립식으로 가정 (적립금 컬럼 존재)
            "initial_capital": initial_v,
            "start_date": pd.to_datetime(first_data.iloc[4]).strftime("%Y-%m-%d"),
            "end_date": pd.to_datetime(last_data.iloc[4]).strftime("%Y-%m-%d"),
            "band_rate": band_rate,
            "monthly_amount": float(first_data.iloc[13]),
            "pool_usage_rate": float(first_data.iloc[16])
        }
        return params
        
    # 2. 기본/간편 템플릿 양식
    df = pd.read_excel(file_path)
    # 0: vr_type, 1: initial_capital, 2: start_date, 3: end_date, 4: band_rate, 5: monthly_amount, 6: pool_usage_rate
    params = {
        "vr_type": str(df.iloc[0, 1]).strip(),
        "initial_capital": float(df.iloc[1, 1]),
        "start_date": str(df.iloc[2, 1]).strip(),
        "end_date": str(df.iloc[3, 1]).strip(),
        "band_rate": float(df.iloc[4, 1]),
        "monthly_amount": float(df.iloc[5, 1])
    }
    if len(df) > 6:
        params["pool_usage_rate"] = float(df.iloc[6, 1])
        
    return params


def export_result(result: VRBacktestResult, file_path: str):
    """백테스트 결과를 엑셀로 내보내기"""
    # 1. 요약 정보
    summary_data = {
        "항목": [
            "VR 방식", "초기 자금", "최종 평가금", "총 수익률", "연 수익률", 
            "최대 낙폭 (MDD)", "총 거래 횟수", "최종 Pool", "최종 보유 주식"
        ],
        "값": [
            result.config.vr_type,
            result.initial_evaluation,
            result.final_evaluation,
            f"{result.total_return:.2%}",
            f"{result.annual_return:.2%}",
            f"{result.max_drawdown:.2%}",
            result.total_trades,
            result.final_pool,
            result.final_shares
        ]
    }
    df_summary = pd.DataFrame(summary_data)
    
    # 2. 일별 데이터
    daily_list = []
    for d in result.daily_data:
        daily_list.append({
            "날짜": d.date.strftime("%Y-%m-%d"),
            "종가": d.close_price,
            "평가금": d.evaluation,
            "V값": d.v_value,
            "최소밴드": d.min_band,
            "최대밴드": d.max_band,
            "현금(Pool)": d.pool,
            "보유주식": d.shares,
            "액션": d.action if d.action else "",
            "거래수량": d.traded_shares
        })
    df_daily = pd.DataFrame(daily_list)
    
    # 3. 사이클 데이터
    cycle_list = []
    for c in result.cycle_data:
        cycle_list.append({
            "사이클": c.cycle_num,
            "시작일": c.start_date.strftime("%Y-%m-%d"),
            "종료일": c.end_date.strftime("%Y-%m-%d"),
            "시작평가금": c.evaluation_start,
            "종료평가금": c.evaluation_end,
            "시작Pool": c.pool_start,
            "종료Pool": c.pool_end,
            "V값": c.v_end, # 해당 사이클 적용 V값
            "최소밴드": c.min_band,
            "최대밴드": c.max_band,
            "수익률": f"{c.price_change_rate:.2%}",
            "매수횟수": c.buy_count,
            "매도횟수": c.sell_count,
            "총거래주식": c.total_traded_shares
        })
    df_cycle = pd.DataFrame(cycle_list)
    
    # 엑셀 파일 쓰기
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        df_summary.to_excel(writer, sheet_name="요약", index=False)
        df_cycle.to_excel(writer, sheet_name="사이클별", index=False)
        df_daily.to_excel(writer, sheet_name="일별상세", index=False)
