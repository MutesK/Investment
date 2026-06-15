import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime

def run_backtest():
    tickers = ["USD", "QLD", "USDKRW=X"]
    print("Downloading data...")
    data = yf.download(tickers, start="2008-01-01")['Close']
    data = data.ffill()
    
    monthly_investment_krw = 400000
    monthly_data = data.resample('ME').last()
    
    all_results = {
        "summary": {},
        "details": {},
        "yearly_performance": []
    }
    
    # Calculate yearly performance for a heatmap-like view
    yearly_data = monthly_data.resample('YE').last().pct_change() * 100
    for year, row in yearly_data.iterrows():
        if not pd.isna(row['USD']):
            all_results["yearly_performance"].append({
                "year": year.year,
                "USD": float(row['USD']),
                "QLD": float(row['QLD']),
                "KRW": float(row['USDKRW=X'])
            })

    for years in range(2, 11):
        window_months = years * 12
        results = []
        num_months = len(monthly_data)
        
        for i in range(num_months - window_months):
            window = monthly_data.iloc[i : i + window_months]
            
            total_usd_shares = 0
            total_qld_shares = 0
            total_invested_krw = 0
            
            for _, row in window.iterrows():
                krw_usd_rate = row['USDKRW=X']
                usd_price = row['USD']
                qld_price = row['QLD']
                if pd.isna(krw_usd_rate) or pd.isna(usd_price) or pd.isna(qld_price): continue
                    
                inv_usd = monthly_investment_krw / krw_usd_rate
                total_usd_shares += inv_usd / usd_price
                total_qld_shares += inv_usd / qld_price
                total_invested_krw += monthly_investment_krw * 2
                
            final_row = monthly_data.iloc[i + window_months]
            final_value_krw = ((total_usd_shares * final_row['USD']) + (total_qld_shares * final_row['QLD'])) * final_row['USDKRW=X']
            return_pct = (final_value_krw / total_invested_krw - 1) * 100
            
            results.append({
                'start': window.index[0].strftime('%Y-%m'),
                'end': final_row.name.strftime('%Y-%m'),
                'return_pct': float(return_pct),
                'final_value': float(final_value_krw)
            })
            
        if results:
            df = pd.DataFrame(results)
            all_results["summary"][f"{years}Y"] = {
                "invested": float(total_invested_krw),
                "max": float(df['return_pct'].max()),
                "min": float(df['return_pct'].min()),
                "avg": float(df['return_pct'].mean()),
                "median": float(df['return_pct'].median()),
                "win_rate": float((df['return_pct'] > 0).mean() * 100),
                "final_avg": float(df['final_value'].mean())
            }
            # Only keep a sample of details to keep JSON size manageable but rich
            all_results["details"][f"{years}Y"] = results[::3] # Every 3rd window
            print(f"Calculated {years}Y windows...")

    with open('backtest_results.json', 'w') as f:
        json.dump(all_results, f, indent=4)
    print("Detailed results saved to backtest_results.json")

if __name__ == "__main__":
    run_backtest()

if __name__ == "__main__":
    run_backtest()
