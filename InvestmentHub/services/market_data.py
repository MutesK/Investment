import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class MarketService:
    @staticmethod
    def get_stock_data(tickers, days):
        if isinstance(tickers, str):
            tickers = [tickers]
            
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            # Always download with auto_adjust=True for cleaner data
            data = yf.download(tickers, start=start_date, end=end_date, progress=False, group_by='column')
            if data.empty:
                return None
            
            # Handle MultiIndex for single ticker vs multiple tickers
            if len(tickers) > 1:
                # yfinance returns MultiIndex like (Price, Ticker)
                # We want a DataFrame where columns are just Tickers (using Close price)
                if 'Close' in data.columns.get_level_values(0):
                    data = data['Close']
            else:
                # Single ticker, columns are Open, High, Low, Close, etc.
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                
            return data
        except Exception as e:
            print(f"Download Error: {e}")
            return None

    @staticmethod
    def calculate_metrics(data, benchmark_data):
        # Daily Returns
        stock_returns = data['Close'].pct_change().dropna()
        benchmark_returns = benchmark_data['Close'].pct_change().dropna()
        
        # Align dates
        combined = pd.concat([stock_returns, benchmark_returns], axis=1).dropna()
        combined.columns = ['Stock', 'Benchmark']
        
        # Beta
        covariance = combined.cov().iloc[0, 1]
        benchmark_variance = combined['Benchmark'].var()
        beta = covariance / benchmark_variance if benchmark_variance != 0 else 0
        
        # Volatility (Annualized)
        volatility = combined['Stock'].std() * np.sqrt(252) * 100
        
        # MDD
        cumulative_returns = (1 + combined['Stock']).cumprod()
        peak = cumulative_returns.cummax()
        drawdown = (cumulative_returns - peak) / peak
        mdd = drawdown.min() * 100
        
        return {
            "beta": round(float(beta), 2),
            "volatility": round(float(volatility), 2),
            "mdd": round(float(mdd), 2)
        }

    @staticmethod
    def get_period_days(period):
        mapping = {"3M": 90, "6M": 180, "1Y": 365}
        if period == "YTD":
            return (datetime.now() - datetime(datetime.now().year, 1, 1)).days
        return mapping.get(period, 365)
