import yfinance as yf
import pandas as pd

def test_div(ticker):
    print(f"\n--- Testing {ticker} ---")
    t = yf.Ticker(ticker)
    
    # Method 1: info
    info = t.info
    yield_info = info.get('dividendYield')
    print(f"Info Yield: {yield_info * 100 if yield_info else 'N/A'}%")
    
    # Method 2: dividends history
    divs = t.dividends
    if not divs.empty:
        # Get last 12 months
        last_year = divs[divs.index > (divs.index[-1] - pd.Timedelta(days=365))]
        total_div = last_year.sum()
        price = info.get('currentPrice') or info.get('previousClose')
        print(f"Calculated Yield (Last 12M): {(total_div / price) * 100 if price else 'N/A'}%")
        
        # Growth
        annual = divs.resample('YE').sum()
        print("Annual Dividends:")
        print(annual.tail(5))
        if len(annual) >= 5:
            growth = (annual.iloc[-2] / annual.iloc[-5])**(1/3) - 1
            print(f"3Y Growth (CAGR): {growth * 100}%")

test_div('SCHD')
test_div('DGRO')
test_div('JEPI')
