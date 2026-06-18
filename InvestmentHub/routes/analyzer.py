from flask import Blueprint, render_template, request, jsonify
from services.market_data import MarketService
import json
import plotly.graph_objects as go
import plotly.utils

analyzer_bp = Blueprint('analyzer', __name__)

@analyzer_bp.route('/analyzer', methods=['GET'])
def index():
    ticker = request.args.get('ticker', '').upper()
    period = request.args.get('period', '1Y')
    
    if not ticker:
        return render_template('analyzer/index.html', ticker=None)

    days = MarketService.get_period_days(period)
    data = MarketService.get_stock_data(ticker, days)
    benchmark = MarketService.get_stock_data('SPY', days)

    if data is None or benchmark is None:
        return render_template('analyzer/index.html', ticker=ticker, error="Data not found")

    # Clean data
    data = data.ffill().dropna()
    benchmark = benchmark.ffill().dropna()

    metrics = MarketService.calculate_metrics(data, benchmark)
    
    # MDD Calculation for Chart
    stock_returns = data['Close'].pct_change().dropna()
    cumulative_returns = (1 + stock_returns).cumprod()
    peak = cumulative_returns.cummax()
    drawdown = (cumulative_returns - peak) / peak * 100

    # Create Candlestick Chart
    # Use tolist() to ensure pure JSON arrays
    fig = go.Figure(data=[go.Candlestick(
        x=data.index.strftime('%Y-%m-%d').tolist(),
        open=data['Open'].tolist(),
        high=data['High'].tolist(),
        low=data['Low'].tolist(),
        close=data['Close'].tolist(),
        name=ticker
    )])
    
    fig.update_layout(
        template="plotly_dark",
        height=500,
        xaxis_rangeslider_visible=False,
        margin=dict(l=40, r=40, t=40, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    # Create MDD Chart
    mdd_fig = go.Figure(data=[go.Scatter(
        x=drawdown.index.strftime('%Y-%m-%d').tolist(),
        y=drawdown.tolist(),
        fill='tozeroy',
        line=dict(color='#ef4444', width=2),
        name='Drawdown (%)'
    )])
    mdd_fig.update_layout(
        template="plotly_dark",
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    mdd_json = json.dumps(mdd_fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('analyzer/index.html', 
                           ticker=ticker, 
                           period=period,
                           metrics=metrics, 
                           graph_json=graph_json,
                           mdd_json=mdd_json)
