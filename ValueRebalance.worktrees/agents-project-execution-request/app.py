"""
ValueRebalance 웹 애플리케이션
Flask 기반 웹 UI
"""
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import pandas as pd

from backtest.vr_backtest import run_backtest
from backtest.visualizer import VRVisualizer
from config import DEFAULT_VR_CONFIG, RECOMMENDED_BANDS

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/api/config')
def get_config():
    """VR 설정 정보 조회"""
    return jsonify({
        "vr_types": {
            k: {
                "name": v["name"],
                "description": v["description"],
                "default_g": v["g"],
                "default_pool_usage_rate": v["pool_usage_rate"]
            }
            for k, v in DEFAULT_VR_CONFIG.items()
        },
        "recommended_bands": RECOMMENDED_BANDS
    })


@app.route('/api/backtest', methods=['POST'])
def run_backtest_api():
    """백테스트 실행"""
    try:
        data = request.json
        
        # 입력 검증
        if not all(k in data for k in ['vr_type', 'initial_capital', 'start_date', 'end_date', 'band_rate']):
            return jsonify({"error": "필수 파라미터 누락"}), 400
        
        vr_type = data.get('vr_type')
        initial_capital = float(data.get('initial_capital'))
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        band_rate = float(data.get('band_rate'))
        monthly_amount = float(data.get('monthly_amount', 0.0))
        
        # 날짜 검증
        try:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            if start >= end:
                return jsonify({"error": "시작 날짜가 종료 날짜보다 이전이어야 합니다."}), 400
        except:
            return jsonify({"error": "잘못된 날짜 형식"}), 400
        
        # 금액 검증
        if initial_capital <= 0:
            return jsonify({"error": "초기 자금은 0보다 커야 합니다."}), 400
        
        # 밴드 검증
        if band_rate <= 0 or band_rate > 1:
            return jsonify({"error": "밴드는 0~1 사이여야 합니다."}), 400
        
        print(f"[백테스트 실행] {vr_type} / {initial_capital} / {start_date} ~ {end_date} / {band_rate}")
        
        # 백테스트 실행
        result = run_backtest(
            vr_type=vr_type,
            initial_capital=initial_capital,
            start_date=start_date,
            end_date=end_date,
            band_rate=band_rate,
            monthly_amount=monthly_amount
        )
        
        # 시각화
        visualizer = VRVisualizer(result)
        chart_html = visualizer.create_chart()
        summary = visualizer.get_summary()
        
        return jsonify({
            "success": True,
            "chart": chart_html,
            "summary": summary,
            "daily_data": [
                {
                    "date": d.date.strftime("%Y-%m-%d"),
                    "close_price": d.close_price,
                    "evaluation": d.evaluation,
                    "v_value": d.v_value,
                    "pool": d.pool,
                    "action": d.action
                }
                for d in result.daily_data
            ]
        })
    
    except Exception as e:
        print(f"[에러] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/scenarios')
def get_scenarios():
    """추천 시나리오 조회"""
    today = datetime.now()
    scenarios = [
        {
            "name": "1년 단기",
            "start_date": (today - timedelta(days=365)).strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "duration": "1년"
        },
        {
            "name": "3년 중기",
            "start_date": (today - timedelta(days=365*3)).strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "duration": "3년"
        },
        {
            "name": "5년 장기",
            "start_date": (today - timedelta(days=365*5)).strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "duration": "5년"
        }
    ]
    return jsonify(scenarios)


if __name__ == '__main__':
    print("=" * 50)
    print("ValueRebalance 웹 서버 시작")
    print("http://localhost:5000 접속")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
