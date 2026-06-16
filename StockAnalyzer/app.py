import streamlit as st
import pandas as pd
from analyzer import get_data, calculate_metrics, get_period_days
from tickers import get_all_tickers
import plotly.graph_objects as go

# Page Config
st.set_page_config(page_title="StockAnalyzer", layout="wide")

st.title("📈 Stock Analyzer")
st.markdown("티커를 입력하거나 선택하여 베타, 변동성, MDD를 확인하세요.")

# Sidebar - Settings
st.sidebar.header("설정")

# 1. 티커 리스트 가져오기
all_tickers = get_all_tickers()

# 2. 티커 입력 방식 제공 (직접 입력 + 선택박스)
st.sidebar.subheader("티커 선택")
user_input = st.sidebar.text_input("1. 직접 입력 (추천)", placeholder="예: AAPL, TSLA, TQQQ...").upper()
selected_from_list = st.sidebar.selectbox(
    "2. 또는 리스트에서 선택 (검색 가능)", 
    options=[""] + all_tickers,
    index=0,
    help="S&P 500, NASDAQ 100 및 주요 ETF를 포함합니다."
)

# 최종 티커 결정
selected_ticker = user_input if user_input else selected_from_list

# 기간 선택 - 폼 내부가 아닌 외부에 있어 변경 시 앱이 재실행됨
period = st.sidebar.radio("기간 선택", ["3M", "6M", "1Y", "YTD"], index=2)

# Main Dashboard
if selected_ticker:
    # st.cache_data를 사용하지 않는 get_data를 호출하므로, 
    # period나 selected_ticker가 바뀌면 streamlit이 이 코드를 다시 실행함
    with st.spinner(f"{selected_ticker} ({period}) 데이터를 분석하는 중..."):
        days = get_period_days(period)
        # 중요: yfinance 데이터가 캐싱되어 차트가 안 바뀔 수 있으므로 
        # get_data 내부에서 기간을 정확히 처리하거나 여기서 확인
        result = get_data(selected_ticker, days)
        
        if result:
            data, benchmark = result
            metrics = calculate_metrics(data, benchmark)
            
            # Metrics Row
            st.header(f"📊 {selected_ticker} 분석 결과 ({period})")
            col1, col2, col3 = st.columns(3)
            col1.metric("Beta (vs SPY)", metrics["Beta"])
            col2.metric("변동성 (Annualized)", f"{metrics['Volatility']}%")
            col3.metric("MDD (Max Drawdown)", f"{metrics['MDD']}%")
            
            # Candlestick Chart
            st.subheader(f"🕯️ 주가 추이 (캔들차트)")
            fig = go.Figure(data=[go.Candlestick(
                x=data.index,
                open=data['Open'].squeeze(),
                high=data['High'].squeeze(),
                low=data['Low'].squeeze(),
                close=data['Close'].squeeze(),
                name=selected_ticker
            )])
            
            fig.update_layout(
                template="plotly_dark", 
                height=600, 
                xaxis_rangeslider_visible=False, # 캔들차트 하단 슬라이더 제외 (깔끔하게)
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Data Table
            with st.expander("최근 데이터 보기"):
                st.write(data.tail(10))
        else:
            st.error(f"'{selected_ticker}' 데이터를 가져올 수 없습니다. 티커와 기간을 확인해 주세요.")
else:
    st.info("왼쪽 사이드바에서 분석할 티커를 입력하거나 선택해 주세요.")
