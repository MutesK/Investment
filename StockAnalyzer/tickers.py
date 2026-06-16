import pandas as pd
import streamlit as st

@st.cache_data
def get_all_tickers():
    # 기본 안전 리스트 (크롤링 실패 시 대비)
    base_tickers = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "UNH", "JNJ",
        "V", "WMT", "JPM", "PG", "MA", "LLY", "CVX", "HD", "ABBV", "KO",
        "SPY", "QQQ", "DIA", "IWM", "VTI", "VOO", "TLT", "TQQQ", "SOXL", "SQQQ"
    ]
    
    try:
        # 1. S&P 500 리스트 가져오기
        sp500_tables = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
        sp500_tickers = sp500_tables[0]['Symbol'].tolist()
        
        # 2. NASDAQ 100 리스트 가져오기
        nasdaq100_tables = pd.read_html('https://en.wikipedia.org/wiki/Nasdaq-100')
        # 위키피디아 구조 변경에 대비해 표 제목이나 인덱스로 찾기 (보통 4번째나 'Ticker' 컬럼이 있는 표)
        nasdaq_tickers = []
        for table in nasdaq100_tables:
            if 'Ticker' in table.columns:
                nasdaq_tickers = table['Ticker'].tolist()
                break
        
        # 3. 추가 주요 ETF 및 인기 종목
        extra_tickers = [
            "TQQQ", "SQQQ", "SOXL", "SOXS", "QLD", "QID", "SPXL", "SPXS",
            "TSLY", "NVDA", "NVDL", "NVDQ", "MSTR", "BITO", "TLT", "TMF"
        ]
        
        # 합치기 및 중복 제거
        all_tickers = list(set(base_tickers + sp500_tickers + nasdaq_tickers + extra_tickers))
        
        # yfinance 호환을 위해 '.'을 '-'로 변경
        all_tickers = [str(t).replace('.', '-') for t in all_tickers]
        
        return sorted(all_tickers)
        
    except Exception as e:
        # 에러 발생 시 로그를 남기고 기본 리스트 반환
        return sorted(list(set(base_tickers)))
