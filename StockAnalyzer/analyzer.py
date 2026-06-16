import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

def get_data(ticker, period_days):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_days)
    
    # Download stock data
    data = yf.download(ticker, start=start_date, end=end_date)
    if data.empty:
        return None
    
    # Handle MultiIndex columns if necessary
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    # Download benchmark data (SPY) for Beta calculation
    benchmark = yf.download("SPY", start=start_date, end=end_date)
    if isinstance(benchmark.columns, pd.MultiIndex):
        benchmark.columns = benchmark.columns.get_level_values(0)
    
    return data, benchmark

def calculate_metrics(data, benchmark):
    # Daily Returns
    stock_returns = data['Close'].pct_change().dropna()
    benchmark_returns = benchmark['Close'].pct_change().dropna()
    
    # Align dates
    combined = pd.concat([stock_returns, benchmark_returns], axis=1).dropna()
    combined.columns = ['Stock', 'Benchmark']
    
    # 1. Beta
    covariance = combined.cov().iloc[0, 1]
    benchmark_variance = combined['Benchmark'].var()
    beta = covariance / benchmark_variance if benchmark_variance != 0 else 0
    
    # 2. Volatility (Annualized Standard Deviation)
    # Assuming 252 trading days
    volatility = combined['Stock'].std() * np.sqrt(252) * 100
    
    # 3. MDD (Maximum Drawdown)
    cumulative_returns = (1 + combined['Stock']).cumprod()
    peak = cumulative_returns.cummax()
    drawdown = (cumulative_returns - peak) / peak
    mdd = drawdown.min() * 100
    
    return {
        "Beta": round(beta, 2),
        "Volatility": round(volatility, 2),
        "MDD": round(mdd, 2)
    }

def get_period_days(period_label):
    if period_label == "3M":
        return 90
    elif period_label == "6M":
        return 180
    elif period_label == "1Y":
        return 365
    elif period_label == "YTD":
        today = datetime.now()
        start_of_year = datetime(today.year, 1, 1)
        return (today - start_of_year).days
    return 365
