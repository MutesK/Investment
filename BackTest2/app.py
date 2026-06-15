import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page Setup
st.set_page_config(page_title="DCA Backtest (QLD & USD)", layout="wide")

st.title("💰 QLD & USD DCA 백테스트 (원화 직투 기준)")
st.markdown("""
이 대시보드는 매월 정해진 원화(KRW) 금액을 **QLD** (ProShares Ultra QLD)와 **USD** (ProShares Ultra Semiconductors)에 적립식으로 투자했을 때의 성과를 분석합니다.
- **QLD**: 나스닥 100 지수의 2배 레버리지
- **USD**: 반도체 지수의 2배 레버리지
""")

# Sidebar Inputs
st.sidebar.header("⚙️ 투자 설정")
start_date = st.sidebar.date_input("투자 시작일", datetime(2015, 1, 1))
end_date = st.sidebar.date_input("투자 종료일", datetime.now())

st.sidebar.subheader("💵 초기 거치액 (원)")
qld_initial_krw = st.sidebar.number_input("QLD 초기 거치액", min_value=0, value=10000000, step=100000, format="%d")
usd_initial_krw = st.sidebar.number_input("USD 초기 거치액", min_value=0, value=5000000, step=100000, format="%d")

st.sidebar.subheader("📅 월별 적립액 (원)")
qld_monthly_krw = st.sidebar.number_input("QLD 월별 적립액", min_value=0, value=600000, step=10000, format="%d")
usd_monthly_krw = st.sidebar.number_input("USD 월별 적립액", min_value=0, value=300000, step=10000, format="%d")

investment_day = st.sidebar.slider("매월 적립일 (일)", 1, 28, 1)

st.sidebar.info("투자일이 휴장일인 경우 다음 거래일에 매수합니다. 초기 거치액은 시작일의 첫 거래일에 전액 매수합니다.")

def get_data(tickers, start, end):
    data = yf.download(tickers, start=start, end=end)['Close']
    return data.ffill().dropna()

if st.sidebar.button("🚀 백테스트 실행"):
    with st.spinner("야후 파이낸스에서 데이터를 불러오는 중..."):
        # Fetch Assets + Benchmark + Exchange Rate
        tickers = ["QLD", "USD", "SPY", "USDKRW=X"]
        raw_data = get_data(tickers, start_date - timedelta(days=5), end_date + timedelta(days=1))
        
        if raw_data.empty:
            st.error("데이터를 가져오지 못했습니다. 기간을 확인하거나 잠시 후 다시 시도해주세요.")
        else:
            # Filter to user selected range
            data = raw_data.loc[start_date:end_date]
            
            # Portfolio Logic
            portfolio = pd.DataFrame(index=data.index)
            portfolio['QLD_Shares'] = 0.0
            portfolio['USD_Shares'] = 0.0
            portfolio['Total_Invested_KRW'] = 0.0
            
            # Benchmark (Lump sum + DCA into SPY)
            portfolio['SPY_Shares'] = 0.0
            
            current_qld_shares = 0.0
            current_usd_shares = 0.0
            current_spy_shares = 0.0
            total_invested_krw = 0.0
            
            investment_history = []
            
            # 1. Initial Investment (Lump Sum)
            first_day = data.index[0]
            rate = data.loc[first_day, 'USDKRW=X']
            
            # Buy QLD & USD Lump Sum
            current_qld_shares += (qld_initial_krw / rate) / data.loc[first_day, 'QLD']
            current_usd_shares += (usd_initial_krw / rate) / data.loc[first_day, 'USD']
            
            # Buy SPY Lump Sum (Benchmark)
            total_initial = qld_initial_krw + usd_initial_krw
            current_spy_shares += (total_initial / rate) / data.loc[first_day, 'SPY']
            
            total_invested_krw += total_initial
            
            portfolio.loc[first_day:, 'QLD_Shares'] = current_qld_shares
            portfolio.loc[first_day:, 'USD_Shares'] = current_usd_shares
            portfolio.loc[first_day:, 'SPY_Shares'] = current_spy_shares
            portfolio.loc[first_day:, 'Total_Invested_KRW'] = total_invested_krw
            
            investment_history.append({
                '구분': '초기거치',
                '날짜': first_day.date(),
                '환율': f"{rate:,.2f}",
                '투자금(원)': f"{total_initial:,.0f}"
            })

            # 2. Monthly DCA
            all_months = pd.date_range(start=start_date, end=end_date, freq='MS')
            
            for m in all_months:
                target_date = m + timedelta(days=investment_day - 1)
                
                # Find the first available trading day on or after the target_date
                available_dates = data.index[data.index >= target_date]
                if len(available_dates) > 0:
                    buy_date = available_dates[0]
                    
                    # Skip if we already bought initial on this day (rare but possible if start_date is investment_day)
                    if buy_date == first_day and total_initial > 0:
                        # But we still want to add the monthly DCA if it's the same day
                        pass
                    
                    # Prices on buy date
                    rate = data.loc[buy_date, 'USDKRW=X']
                    total_monthly = qld_monthly_krw + usd_monthly_krw
                    
                    current_qld_shares += (qld_monthly_krw / rate) / data.loc[buy_date, 'QLD']
                    current_usd_shares += (usd_monthly_krw / rate) / data.loc[buy_date, 'USD']
                    current_spy_shares += (total_monthly / rate) / data.loc[buy_date, 'SPY']
                    
                    total_invested_krw += total_monthly
                    
                    portfolio.loc[buy_date:, 'QLD_Shares'] = current_qld_shares
                    portfolio.loc[buy_date:, 'USD_Shares'] = current_usd_shares
                    portfolio.loc[buy_date:, 'SPY_Shares'] = current_spy_shares
                    portfolio.loc[buy_date:, 'Total_Invested_KRW'] = total_invested_krw
                    
                    investment_history.append({
                        '구분': '매월적립',
                        '날짜': buy_date.date(),
                        '환율': f"{rate:,.2f}",
                        '투자금(원)': f"{total_monthly:,.0f}"
                    })

            # Daily Valuation
            portfolio['QLD_Val_KRW'] = portfolio['QLD_Shares'] * data['QLD'] * data['USDKRW=X']
            portfolio['USD_Val_KRW'] = portfolio['USD_Shares'] * data['USD'] * data['USDKRW=X']
            portfolio['Total_Val_KRW'] = portfolio['QLD_Val_KRW'] + portfolio['USD_Val_KRW']
            portfolio['SPY_Val_KRW'] = portfolio['SPY_Shares'] * data['SPY'] * data['USDKRW=X']

            # Results Display
            final_val = portfolio['Total_Val_KRW'].iloc[-1]
            total_inv = portfolio['Total_Invested_KRW'].iloc[-1]
            profit = final_val - total_inv
            roi = (profit / total_inv * 100) if total_inv > 0 else 0
            
            spy_final_val = portfolio['SPY_Val_KRW'].iloc[-1]
            spy_roi = ((spy_final_val - total_inv) / total_inv * 100) if total_inv > 0 else 0

            st.subheader("📊 백테스트 결과 요약")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("최종 자산 (원)", f"{final_val:,.0f}")
            m2.metric("총 투자원금 (원)", f"{total_inv:,.0f}")
            m3.metric("누적 수익률", f"{roi:.1f}%", f"{roi-spy_roi:+.1f}% vs SPY")
            m4.metric("최종 수익 (원)", f"{profit:,.0f}")

            # Main Chart
            st.subheader("📈 자산 성장 곡선 (원화 기준)")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=portfolio.index, y=portfolio['Total_Val_KRW'], name='내 포트폴리오 (QLD+USD)', line=dict(color='#1f77b4', width=3)))
            fig.add_trace(go.Scatter(x=portfolio.index, y=portfolio['SPY_Val_KRW'], name='벤치마크 (SPY)', line=dict(color='#ff7f0e', dash='dot')))
            fig.add_trace(go.Scatter(x=portfolio.index, y=portfolio['Total_Invested_KRW'], name='누적 투자원금', fill='tozeroy', line=dict(color='rgba(200,200,200,0.5)')))
            
            fig.update_layout(hovermode="x unified", yaxis_tickformat=',d', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig, use_container_width=True)

            # Asset Allocation Chart
            st.subheader("⚖️ 자산별 평가액 비중")
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=portfolio.index, y=portfolio['QLD_Val_KRW'], name='QLD', stackgroup='one'))
            fig2.add_trace(go.Scatter(x=portfolio.index, y=portfolio['USD_Val_KRW'], name='USD', stackgroup='one'))
            fig2.update_layout(hovermode="x unified", yaxis_tickformat=',d')
            st.plotly_chart(fig2, use_container_width=True)

            # Drawdown (MDD) - Simplified
            rolling_max = portfolio['Total_Val_KRW'].cummax()
            drawdown = (portfolio['Total_Val_KRW'] - rolling_max) / rolling_max * 100
            mdd = drawdown.min()
            
            st.subheader("📉 리스크 분석")
            st.write(f"**최대 낙폭 (MDD):** {mdd:.2f}%")
            
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=portfolio.index, y=drawdown, name='Drawdown', fill='tozeroy', line=dict(color='red')))
            fig3.update_layout(title="Drawdown (%)", yaxis_title="Percentage")
            st.plotly_chart(fig3, use_container_width=True)

            # History
            with st.expander("📝 상세 매수 내역"):
                st.table(pd.DataFrame(investment_history).iloc[::-1]) # Show latest first

else:
    st.info("좌측 사이드바에서 투자 조건을 설정한 후 '백테스트 실행' 버튼을 클릭하세요.")
