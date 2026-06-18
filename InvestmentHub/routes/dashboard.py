from flask import Blueprint, render_template, request, redirect, url_for, flash
import pandas as pd
from database import db
from models import AssetStatus, LedgerTransaction, NetWorthSnapshot

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    # Fetch Asset Status
    assets = AssetStatus.query.all()
    
    # Calculate totals
    total_assets = sum(a.value for a in assets if a.category != '대출')
    total_debt = sum(a.value for a in assets if a.category == '대출')
    net_assets = total_assets - total_debt
    
    total_investment_principal = sum(a.principal for a in assets if a.category == '투자')
    total_investment_value = sum(a.value for a in assets if a.category == '투자')
    investment_return = 0
    if total_investment_principal > 0:
        investment_return = ((total_investment_value / total_investment_principal) - 1) * 100

    # Historical Net Worth from actual snapshots & Benchmark Comparison
    chart_dates = []
    asset_pcts = []
    spy_pcts = []
    kospi_pcts = []
    
    try:
        snapshots = NetWorthSnapshot.query.order_by(NetWorthSnapshot.date.asc()).all()
        if len(snapshots) >= 2:
            import yfinance as yf
            from datetime import datetime, timedelta
            
            start_date = snapshots[0].date
            end_date = snapshots[-1].date
            base_nw = snapshots[0].net_worth if snapshots[0].net_worth > 0 else 1
            
            end_date_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            end_date_yf = end_date_dt.strftime("%Y-%m-%d")
            
            # Fetch benchmark data
            spy_data = yf.download("SPY", start=start_date, end=end_date_yf)
            kospi_data = yf.download("^KS11", start=start_date, end=end_date_yf)
            
            spy_close = spy_data['Close'].ffill().bfill()
            kospi_close = kospi_data['Close'].ffill().bfill()
            if isinstance(spy_close, pd.DataFrame): spy_close = spy_close.iloc[:, 0]
            if isinstance(kospi_close, pd.DataFrame): kospi_close = kospi_close.iloc[:, 0]
            
            start_spy = float(spy_close.iloc[0]) if len(spy_close) > 0 else 1
            start_kospi = float(kospi_close.iloc[0]) if len(kospi_close) > 0 else 1
            
            # Build chart data from snapshots
            for snap in snapshots:
                chart_dates.append(snap.date)
                asset_pcts.append(((snap.net_worth / base_nw) - 1) * 100)
                
                # Find closest benchmark data
                snap_dt = pd.Timestamp(snap.date)
                try:
                    spy_idx = spy_close.index.get_indexer([snap_dt], method='ffill')[0]
                    kospi_idx = kospi_close.index.get_indexer([snap_dt], method='ffill')[0]
                    s_val = float(spy_close.iloc[spy_idx]) if spy_idx >= 0 else start_spy
                    k_val = float(kospi_close.iloc[kospi_idx]) if kospi_idx >= 0 else start_kospi
                except:
                    s_val = start_spy
                    k_val = start_kospi
                
                spy_pcts.append(((s_val / start_spy) - 1) * 100)
                kospi_pcts.append(((k_val / start_kospi) - 1) * 100)
                
        elif len(snapshots) == 1:
            # Only one snapshot - show a single point at 0%
            chart_dates.append(snapshots[0].date)
            asset_pcts.append(0.0)
            spy_pcts.append(0.0)
            kospi_pcts.append(0.0)
    except Exception as e:
        print("Chart calculation error:", e)

    # Categorize for charts/lists
    real_estate = [a for a in assets if a.category == '부동산']
    investments = [a for a in assets if a.category == '투자']
    accounts = [a for a in assets if a.category == '계좌']
    
    stats = [
        {"label": "순자산 (Net Worth)", "value": f"{net_assets:,.0f} 원", "change": "", "positive": True},
        {"label": "총 자산 (Total Assets)", "value": f"{total_assets:,.0f} 원", "change": "", "positive": True},
        {"label": "투자 평가액", "value": f"{total_investment_value:,.0f} 원", "change": f"{investment_return:+.2f}%", "positive": investment_return >= 0},
        {"label": "총 부채 (Debt)", "value": f"{total_debt:,.0f} 원", "change": "", "positive": False},
    ]
    
    # Investment Chart Data
    inv_labels = [i.name for i in investments if i.value > 0]
    inv_values = [i.value for i in investments if i.value > 0]

    return render_template('index.html', stats=stats, investments=investments, 
                           inv_labels=inv_labels, inv_values=inv_values,
                           real_estate=real_estate, accounts=accounts,
                           chart_dates=chart_dates, asset_pcts=asset_pcts,
                           spy_pcts=spy_pcts, kospi_pcts=kospi_pcts)

@dashboard_bp.route('/upload_excel', methods=['POST'])
def upload_excel():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('dashboard.index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('dashboard.index'))
    
    if file and file.filename.endswith('.xlsx'):
        try:
            # 1. Parse '가계부 내역' (Ledger)
            df_ledger = pd.read_excel(file, sheet_name='가계부 내역', engine='openpyxl')
            df_ledger = df_ledger.fillna('')
            
            added_count = 0
            for index, row in df_ledger.iterrows():
                date = str(row['날짜'])[:10] if row['날짜'] else ''
                time_str = str(row['시간']) if row['시간'] else ''
                tx_type = str(row['타입'])
                main_cat = str(row['대분류'])
                sub_cat = str(row['소분류'])
                desc = str(row['내용'])
                amount = float(row['금액']) if row['금액'] != '' else 0.0
                currency = str(row['화폐'])
                pay_method = str(row['결제수단'])
                memo = str(row['메모'])
                
                existing = LedgerTransaction.query.filter_by(
                    date=date, time=time_str, amount=amount, description=desc
                ).first()
                
                if not existing:
                    new_tx = LedgerTransaction(
                        date=date, time=time_str, tx_type=tx_type,
                        main_category=main_cat, sub_category=sub_cat,
                        description=desc, amount=amount, currency=currency,
                        payment_method=pay_method, memo=memo
                    )
                    db.session.add(new_tx)
                    added_count += 1

            # 2. Parse '뱅샐현황' (Asset Status)
            df_assets = pd.read_excel(file, sheet_name='뱅샐현황', engine='openpyxl')
            df_assets = df_assets.fillna('')
            
            # Clear old asset data
            AssetStatus.query.delete()
            
            current_section = None
            for index, row in df_assets.iterrows():
                col1 = str(row.iloc[1]).strip() if len(row) > 1 else ''
                col2 = str(row.iloc[2]).strip() if len(row) > 2 else ''
                
                if '3.재무현황' in col1:
                    current_section = '자산'
                    continue
                elif '4.보험현황' in col1:
                    current_section = '보험'
                    continue
                elif '5.투자현황' in col1:
                    current_section = '투자'
                    continue
                elif '6.대출현황' in col1:
                    current_section = '대출'
                    continue
                
                if current_section == '자산':
                    # Real Estate
                    if col1 == '부동산':
                        val_str = str(row.iloc[4]) if len(row) > 4 else '0'
                        try:
                            val = float(val_str)
                            db.session.add(AssetStatus(category='부동산', name=col2, value=val))
                        except: pass
                    # Accounts
                    elif col2 in ['기본계좌', '연금저축', '중개형ISA', '위탁계좌', '종합계좌', '종합위탁']:
                        val_str = str(row.iloc[4]) if len(row) > 4 else '0'
                        try:
                            val = float(val_str)
                            if val > 0:
                                db.session.add(AssetStatus(category='계좌', name=col2, value=val))
                        except: pass

                elif current_section == '투자':
                    if col1 in ['주식', '펀드', '채권', '암호화폐']:
                        inst = col2
                        name = str(row.iloc[3]).strip() if len(row) > 3 else ''
                        prin_str = str(row.iloc[5]).replace(',','') if len(row) > 5 else '0'
                        val_str = str(row.iloc[6]).replace(',','') if len(row) > 6 else '0'
                        ret_str = str(row.iloc[7]).replace(',','') if len(row) > 7 else '0'
                        try:
                            prin = float(prin_str) if prin_str else 0.0
                            val = float(val_str) if val_str else 0.0
                            ret = float(ret_str) if ret_str else 0.0
                            db.session.add(AssetStatus(category='투자', institution=inst, name=name, principal=prin, value=val, return_rate=ret))
                        except: pass

                elif current_section == '대출':
                    if col1 not in ['', '총계', '대출종류']:
                        inst = col2
                        name = str(row.iloc[3]).strip() if len(row) > 3 else ''
                        val_str = str(row.iloc[6]).replace(',','') if len(row) > 6 else '0' # 대출잔액
                        try:
                            val = float(val_str) if val_str else 0.0
                            if val > 0:
                                db.session.add(AssetStatus(category='대출', institution=inst, name=name, value=val))
                        except: pass

            db.session.commit()
            
            # 3. Save a NetWorthSnapshot for this upload
            recalc_assets = AssetStatus.query.all()
            snap_total_assets = sum(a.value for a in recalc_assets if a.category != '대출')
            snap_total_debt = sum(a.value for a in recalc_assets if a.category == '대출')
            snap_net_worth = snap_total_assets - snap_total_debt
            
            from datetime import date as date_cls
            today_str = date_cls.today().strftime('%Y-%m-%d')
            
            existing_snap = NetWorthSnapshot.query.filter_by(date=today_str).first()
            if existing_snap:
                existing_snap.net_worth = snap_net_worth
                existing_snap.total_assets = snap_total_assets
                existing_snap.total_debt = snap_total_debt
            else:
                db.session.add(NetWorthSnapshot(
                    date=today_str,
                    net_worth=snap_net_worth,
                    total_assets=snap_total_assets,
                    total_debt=snap_total_debt
                ))
            db.session.commit()
            
            flash(f'Successfully imported {added_count} new transactions and updated Asset Status.', 'success')
            
        except Exception as e:
            flash(f'Error parsing file: {str(e)}', 'error')
            
    else:
        flash('Invalid file format. Please upload an .xlsx file.', 'error')
        
    return redirect(url_for('dashboard.index'))
