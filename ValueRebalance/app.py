"""
ValueRebalance 웹 애플리케이션
Flask 기반 웹 UI
"""
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import os

from manager.portfolio_manager import PortfolioManager

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

pm = PortfolioManager()

@app.route('/')
def index():
    """매니저 메인 페이지"""
    return render_template('manager.html')

@app.route('/api/portfolio')
def get_portfolio():
    """포트폴리오 전체 데이터 조회"""
    # 통합 자산 계산 (간단히 원화 합산)
    total_eval = 0
    for name, asset in pm.data["assets"].items():
        # 실제로는 여기서 yfinance로 현재가를 가져와 합산해야 함
        total_eval += asset["state"]["shares"] * 10000 + asset["state"]["pool"] # 임시 계산
        
    return jsonify({
        "portfolio": pm.data,
        "summary": {
            "total_eval_krw": total_eval,
            "total_eval_usd": total_eval / 1350 # 임시 환율
        }
    })

@app.route('/api/asset/<name>/guide')
def get_asset_guide(name):
    """특정 자산의 오늘 주문 가이드"""
    guide = pm.get_order_guide(name)
    return jsonify(guide)

@app.route('/api/asset/update', methods=['POST'])
def update_asset():
    """자산 상태 업데이트 (주식수, 현금 등)"""
    data = request.json
    pm.update_asset_state(
        name=data['name'],
        shares=data.get('shares'),
        pool=data.get('pool'),
        v_value=data.get('v_value')
    )
    return jsonify({"success": True})

@app.route('/api/asset/settings', methods=['POST'])
def update_asset_settings():
    """자산 전략 설정 업데이트 (G값, Pool 사용비율 등)"""
    data = request.json
    pm.update_asset_settings(
        name=data['name'],
        vr_type=data.get('vr_type'),
        g=float(data.get('g')),
        band_rate=float(data.get('band_rate')),
        pool_usage_rate=float(data.get('pool_usage_rate')),
        monthly_amount=float(data.get('monthly_amount', 0))
    )
    return jsonify({"success": True})

if __name__ == '__main__':
    print("=" * 50)
    print("ValueRebalance Live Manager 시작")
    print("http://localhost:5001 접속")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5001)
