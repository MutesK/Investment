from flask import Blueprint, render_template, request, jsonify
from services.market_data import MarketService
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

dividend_bp = Blueprint('dividend', __name__)

@dividend_bp.route('/dividend')
def index():
    return render_template('dividend/index.html')

@dividend_bp.route('/dividend/analyze', methods=['POST'])
def analyze():
    params = request.json
    tickers = params.get('tickers', ['SCHD', 'JEPI', 'DGRO'])
    
    results = {}
    import yfinance as yf
    
    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            info = t.info
            divs = t.dividends
            
            if divs.empty:
                results[ticker] = {"error": "No dividend data"}
                continue

            # 1. Calculate Current Yield
            # yfinance info['dividendYield'] can be 0.0325 (3.25%) OR 3.25 depending on ticker/time
            yield_raw = info.get('dividendYield') or info.get('trailingAnnualDividendYield')
            
            if yield_raw:
                # If yield is > 1.0 (e.g. 3.25), it's already a percentage.
                # If it's < 1.0 (e.g. 0.0325), it's a decimal that needs * 100.
                # NOTE: Extremely high yields (>100%) are rare, so we use 1.0 as threshold.
                if yield_raw < 1.0:
                    yield_pct = yield_raw * 100
                else:
                    yield_pct = yield_raw
            else:
                # Manual calculation: Sum last 4 dividend payments (assuming quarterly)
                # or last year's total. Let's use last 12 months for safety.
                last_year_divs = divs[divs.index > (datetime.now() - timedelta(days=365))]
                total_div_1y = last_year_divs.sum()
                
                # Fetch price from various possible fields
                price = info.get('currentPrice') or info.get('previousClose') or info.get('navPrice')
                if not price:
                    # Fallback to fetching latest price from history
                    hist = t.history(period="1d")
                    if not hist.empty:
                        price = hist['Close'].iloc[-1]
                
                yield_pct = (total_div_1y / price * 100) if (price and price > 0) else 0

            # 2. Calculate 3Y Dividend Growth (CAGR)
            # Use only full years to avoid current partial year distortion
            current_year = datetime.now().year
            divs_annual = divs.resample('YE').sum()
            full_years = divs_annual[divs_annual.index.year < current_year]
            
            if len(full_years) >= 4:
                # Latest full year / Full year 3 years ago
                # e.g., 2025 / 2022
                v_final = full_years.iloc[-1]
                v_start = full_years.iloc[-4]
                if v_start > 0:
                    cagr = (pow(v_final / v_start, 1/3) - 1) * 100
                else:
                    cagr = 0
            else:
                cagr = 0

            results[ticker] = {
                "yield": round(float(yield_pct), 2),
                "growth_3y": round(float(cagr), 2),
                "latest_annual": round(float(divs.resample('YE').sum().iloc[-2] if len(divs_annual) > 1 else 0), 2)
            }
        except Exception as e:
            results[ticker] = {"error": str(e)}
        
    return jsonify(results)
