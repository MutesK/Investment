from flask import Flask, render_template
import os
from database import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///investment_hub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)

db.init_app(app)

# Import routes (Blueprints)
from routes.dashboard import dashboard_bp
from routes.analyzer import analyzer_bp
from routes.backtest import backtest_bp
from routes.portfolio import portfolio_bp
from routes.dividend import dividend_bp
from routes.ledger import ledger_bp

from models import VRAsset # Ensure models are tracked

app.register_blueprint(dashboard_bp)
app.register_blueprint(analyzer_bp)
app.register_blueprint(backtest_bp)
app.register_blueprint(portfolio_bp)
app.register_blueprint(dividend_bp)
app.register_blueprint(ledger_bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
