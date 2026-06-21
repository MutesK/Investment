from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from database import db
from models import LedgerTransaction
import pandas as pd
import os

ledger_bp = Blueprint('ledger', __name__, url_prefix='/ledger')

@ledger_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    category_filter = request.args.get('category', '')
    tx_type_filter = request.args.get('tx_type', '')
    sort_amount = request.args.get('sort_amount', '')
    
    # Get distinct months and years for the filter dropdowns
    dates = db.session.query(LedgerTransaction.date).distinct().all()
    months = sorted(list(set(d[0][:7] for d in dates if d[0])), reverse=True)
    years = sorted(list(set(d[0][:4] for d in dates if d[0])), reverse=True)
    
    view_type = request.args.get('view_type', 'month')
    month_filter = request.args.get('month', None)
    year_filter = request.args.get('year', None)
    
    # Default to the most recent period if visiting for the first time
    if view_type == 'month':
        if month_filter is None:
            month_filter = months[0] if months else ''
        elif month_filter == 'all':
            month_filter = ''
        year_filter = ''
    else:
        if year_filter is None:
            year_filter = years[0] if years else ''
        elif year_filter == 'all':
            year_filter = ''
        month_filter = ''
        
    # Base query for the current view
    base_query = LedgerTransaction.query
    if view_type == 'month' and month_filter:
        base_query = base_query.filter(LedgerTransaction.date.startswith(month_filter))
    elif view_type == 'year' and year_filter:
        base_query = base_query.filter(LedgerTransaction.date.startswith(year_filter))
    
    # Fetch transactions for summary calculations (filtered by period)
    summary_transactions = base_query.all()
    
    # Calculate summaries
    total_income = sum(t.amount for t in summary_transactions if t.tx_type == '수입')
    total_expense = sum(t.amount for t in summary_transactions if t.tx_type == '지출')
    net_flow = total_income + total_expense
    
    # Prepare data for charts (e.g. expenses by category)
    expense_data = {}
    for t in summary_transactions:
        if t.tx_type == '지출':
            cat = t.main_category
            expense_data[cat] = expense_data.get(cat, 0) + abs(t.amount)
            
    # sort expense data descending
    sorted_expense = sorted(expense_data.items(), key=lambda x: x[1], reverse=True)
    expense_labels = [item[0] for item in sorted_expense]
    expense_values = [item[1] for item in sorted_expense]
 
    # Get distinct categories for the filter dropdown
    categories = sorted(list(set(t.main_category for t in summary_transactions if t.main_category)))
 
    # Query for the table with optional category and tx_type filters
    table_query = base_query
    if category_filter:
        table_query = table_query.filter(LedgerTransaction.main_category == category_filter)
    if tx_type_filter:
        table_query = table_query.filter(LedgerTransaction.tx_type == tx_type_filter)
        
    # Apply sorting
    if sort_amount == 'desc':
        table_query = table_query.order_by(LedgerTransaction.amount.desc())
    elif sort_amount == 'asc':
        table_query = table_query.order_by(LedgerTransaction.amount.asc())
    else:
        table_query = table_query.order_by(LedgerTransaction.date.desc(), LedgerTransaction.time.desc())
        
    # Paginate transactions for the list
    pagination = table_query.paginate(page=page, per_page=20, error_out=False)
 
    return render_template('ledger.html', 
                           pagination=pagination,
                           total_income=total_income,
                           total_expense=abs(total_expense),
                           net_flow=net_flow,
                           expense_labels=expense_labels,
                           expense_values=expense_values,
                           categories=categories,
                           current_category=category_filter,
                           months=months,
                           years=years,
                           view_type=view_type,
                           current_month=month_filter or ('all' if month_filter == '' else ''),
                           current_year=year_filter or ('all' if year_filter == '' else ''),
                           current_tx_type=tx_type_filter,
                           current_sort=sort_amount)

@ledger_bp.route('/update/<int:tx_id>', methods=['POST'])
def update_transaction(tx_id):
    tx = LedgerTransaction.query.get_or_404(tx_id)
    data = request.get_json()
    
    if 'main_category' in data:
        tx.main_category = data['main_category']
    if 'sub_category' in data:
        tx.sub_category = data['sub_category']
    
    db.session.commit()
    return jsonify({'success': True, 'main_category': tx.main_category, 'sub_category': tx.sub_category})

@ledger_bp.route('/delete/<int:tx_id>', methods=['POST'])
def delete_transaction(tx_id):
    tx = LedgerTransaction.query.get_or_404(tx_id)
    db.session.delete(tx)
    db.session.commit()
    return jsonify({'success': True})
