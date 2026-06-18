from flask import Blueprint, render_template, request, jsonify
from services.market_data import MarketService
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.utils
import json
from datetime import datetime, timedelta

backtest_bp = Blueprint('backtest', __name__)

@backtest_bp.route('/backtest', methods=['GET'])
def index():
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('backtest/index.html', today_date=today)

@backtest_bp.route('/backtest/run/dca', methods=['POST'])
def run_dca():
    params = request.json
    assets = params.get('assets', [])
    start_date = params.get('start_date', '2015-01-01')
    end_date = params.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    investment_day = int(params.get('investment_day', 1))

    if not assets:
        return jsonify({"error": "No assets provided"}), 400

    # Collect all unique tickers including SPY and FX
    tickers = list(set([a['ticker'] for a in assets] + ['SPY', 'USDKRW=X']))
    
    # Calculate days to fetch
    fetch_days = (datetime.now() - datetime.strptime(start_date, '%Y-%m-%d')).days + 30
    all_data = MarketService.get_stock_data(tickers, fetch_days)
    
    if all_data is None:
        return jsonify({"error": "Failed to fetch market data"}), 400

    # Check for missing tickers
    missing = [t for t in tickers if t not in all_data.columns]
    if missing:
        return jsonify({"error": f"Missing data for: {', '.join(missing)}"}), 400

    data = all_data.loc[start_date:end_date].ffill().dropna()
    if data.empty:
        return jsonify({"error": "No data for selected range after cleaning"}), 400

    # Backtest Logic
    valuation = pd.DataFrame(index=data.index)
    valuation['total_val'] = 0.0
    valuation['shares_spy'] = 0.0
    valuation['invested'] = 0.0
    
    # Initialize asset share columns
    for a in assets:
        valuation[f"shares_{a['ticker']}"] = 0.0

    first_day = data.index[0]
    rate = data.loc[first_day, 'USDKRW=X']
    
    # Initial Investment
    total_initial = 0
    for a in assets:
        shares = (float(a['initial']) / rate) / data.loc[first_day, a['ticker']]
        valuation.loc[first_day:, f"shares_{a['ticker']}"] = shares
        total_initial += float(a['initial'])
    
    valuation.loc[first_day:, 'invested'] = total_initial
    valuation.loc[first_day:, 'shares_spy'] = (total_initial / rate) / data.loc[first_day, 'SPY']

    # Monthly DCA
    all_months = pd.date_range(start=start_date, end=end_date, freq='MS')
    for m in all_months:
        target = m + timedelta(days=investment_day - 1)
        available = data.index[data.index >= target]
        if len(available) > 0:
            buy_date = available[0]
            if buy_date == first_day: continue
            
            rate = data.loc[buy_date, 'USDKRW=X']
            total_monthly = 0
            for a in assets:
                monthly_shares = (float(a['monthly']) / rate) / data.loc[buy_date, a['ticker']]
                valuation.loc[buy_date:, f"shares_{a['ticker']}"] += monthly_shares
                total_monthly += float(a['monthly'])
            
            valuation.loc[buy_date:, 'shares_spy'] += (total_monthly / rate) / data.loc[buy_date, 'SPY']
            valuation.loc[buy_date:, 'invested'] += total_monthly

    # Calculate Total Value (Daily)
    total_val_series = pd.Series(0.0, index=valuation.index)
    for a in assets:
        ticker = a['ticker']
        total_val_series += valuation[f"shares_{ticker}"] * data[ticker] * data['USDKRW=X']
    
    valuation['total_val'] = total_val_series
    valuation['spy_val'] = valuation['shares_spy'] * data['SPY'] * data['USDKRW=X']

    # Metrics
    final_val = float(valuation['total_val'].iloc[-1])
    total_inv = float(valuation['invested'].iloc[-1])
    roi = ((final_val / total_inv) - 1) * 100 if total_inv > 0 else 0
    spy_roi = ((float(valuation['spy_val'].iloc[-1]) / total_inv) - 1) * 100 if total_inv > 0 else 0
    
    # MDD
    rolling_max = valuation['total_val'].cummax()
    drawdown = (valuation['total_val'] - rolling_max) / rolling_max * 100
    mdd = float(drawdown.min())

    # Chart - Use explicit lists to avoid serialization issues
    x_data = valuation.index.strftime('%Y-%m-%d').tolist()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_data, 
        y=valuation['total_val'].tolist(), 
        name='Portfolio', 
        line=dict(color='#3b82f6', width=3),
        hovertemplate='Portfolio: ₩%{y:,.0f}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=x_data, 
        y=valuation['spy_val'].tolist(), 
        name='SPY (Benchmark)', 
        line=dict(color='#94a3b8', dash='dot'),
        hovertemplate='SPY: ₩%{y:,.0f}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=x_data, 
        y=valuation['invested'].tolist(), 
        name='Invested', 
        fill='tozeroy', 
        line=dict(color='rgba(100,116,139,0.1)'),
        hovertemplate='Invested: ₩%{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        template="plotly_dark",
        hovermode="x unified",
        xaxis_title="Date",
        yaxis_title="Value (KRW)",
        yaxis_tickformat=',d',
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return jsonify({
        "summary": {
            "final_value": f"{final_val:,.0f}",
            "invested": f"{total_inv:,.0f}",
            "roi": f"{roi:.2f}%",
            "spy_roi": f"{spy_roi:.2f}%",
            "mdd": f"{mdd:.2f}%"
        },
        "chart": json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))
    })

@backtest_bp.route('/backtest/run/rolling', methods=['POST'])
def run_rolling():
    pass
