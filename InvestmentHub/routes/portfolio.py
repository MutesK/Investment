from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from models import VRAsset
from database import db
from services.vr_engine import VREngine
from services.market_data import MarketService
from datetime import datetime

portfolio_bp = Blueprint('portfolio', __name__)

@portfolio_bp.route('/portfolio')
def index():
    assets = VRAsset.query.all()
    return render_template('portfolio/index.html', assets=assets)

@portfolio_bp.route('/portfolio/add', methods=['POST'])
def add_asset():
    data = request.form
    ticker = data.get('ticker').upper()
    
    # Check if already exists
    if VRAsset.query.filter_by(ticker=ticker).first():
        return redirect(url_for('portfolio.index'))
        
    new_asset = VRAsset(
        ticker=ticker,
        name=data.get('name', ticker),
        shares=float(data.get('shares', 0)),
        pool=float(data.get('pool', 0)),
        v_value=float(data.get('v_value', 0)),
        vr_type=data.get('vr_type', 'ACCUMULATION'),
        g_value=float(data.get('g_value', 10)),
        band_ratio=float(data.get('band_ratio', 0.15)),
        monthly_extra=float(data.get('monthly_extra', 0))
    )
    
    # If v_value is 0, initialize it with current evaluation
    if new_asset.v_value == 0:
        market_data = MarketService.get_stock_data(ticker, 1)
        if market_data is not None:
            price = market_data['Close'].iloc[-1]
            new_asset.v_value = price * new_asset.shares

    db.session.add(new_asset)
    db.session.commit()
    return redirect(url_for('portfolio.index'))

@portfolio_bp.route('/portfolio/asset/<int:asset_id>/guide')
def get_guide(asset_id):
    asset = VRAsset.query.get_or_404(asset_id)
    
    # Get current price
    market_data = MarketService.get_stock_data(asset.ticker, 1)
    if market_data is None:
        return jsonify({"error": "Failed to fetch market price"}), 400
        
    current_price = float(market_data['Close'].iloc[-1])
    current_eval = current_price * asset.shares
    
    table = VREngine.get_trading_table(
        asset.shares, asset.pool, asset.v_value, 
        asset.band_ratio, asset.pool_limit
    )
    
    return jsonify({
        "ticker": asset.ticker,
        "current_price": current_price,
        "current_eval": current_eval,
        "v_value": asset.v_value,
        "guide": table
    })

@portfolio_bp.route('/portfolio/asset/<int:asset_id>/next-cycle', methods=['POST'])
def next_cycle(asset_id):
    asset = VRAsset.query.get_or_404(asset_id)
    
    market_data = MarketService.get_stock_data(asset.ticker, 1)
    if market_data is None:
        return jsonify({"error": "Failed to fetch market price"}), 400
        
    current_price = float(market_data['Close'].iloc[-1])
    current_eval = current_price * asset.shares
    
    # Calculate next V
    # V_next = V_before + Pool / G + (E - V_before) / 2 * sqrt(G) + extra
    new_v = VREngine.calculate_next_v(
        asset.v_value, asset.pool, asset.g_value, 
        current_eval, asset.monthly_extra
    )
    
    # Add monthly extra to pool
    asset.v_value = new_v
    asset.pool += asset.monthly_extra
    
    db.session.commit()
    return jsonify({"success": True, "new_v": new_v})

@portfolio_bp.route('/portfolio/asset/<int:asset_id>/update', methods=['POST'])
def update_state(asset_id):
    asset = VRAsset.query.get_or_404(asset_id)
    data = request.json
    
    if 'shares' in data: asset.shares = float(data['shares'])
    if 'pool' in data: asset.pool = float(data['pool'])
    if 'v_value' in data: asset.v_value = float(data['v_value'])
    if 'vr_type' in data: asset.vr_type = data['vr_type']
    
    db.session.commit()
    return jsonify({"success": True})

@portfolio_bp.route('/portfolio/asset/<int:asset_id>/delete', methods=['POST'])
def delete_asset(asset_id):
    asset = VRAsset.query.get_or_404(asset_id)
    db.session.delete(asset)
    db.session.commit()
    return jsonify({"success": True})
