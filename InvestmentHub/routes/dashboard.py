from flask import Blueprint, render_template

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    # Mock data for the "cool" index page
    stats = [
        {"label": "Total Assets", "value": "$124,500", "change": "+12.5%", "positive": True},
        {"label": "Monthly Profit", "value": "$3,240", "change": "+5.2%", "positive": True},
        {"label": "Active Strategies", "value": "4", "change": "0", "positive": True},
        {"label": "Risk Level", "value": "Moderate", "change": "Stable", "positive": True},
    ]
    return render_template('index.html', stats=stats)
