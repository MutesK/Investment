from database import db
from datetime import datetime

class VRAsset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100))
    shares = db.Column(db.Float, default=0.0)
    pool = db.Column(db.Float, default=0.0)
    v_value = db.Column(db.Float, default=0.0)
    
    # Strategy Settings
    vr_type = db.Column(db.String(20), default='ACCUMULATION') # ACCUMULATION, DEFERRAL, WITHDRAWAL
    g_value = db.Column(db.Float, default=10.0)
    band_ratio = db.Column(db.Float, default=0.15)
    pool_limit = db.Column(db.Float, default=0.75)
    monthly_extra = db.Column(db.Float, default=0.0)
    
    # Cycle Info
    cycle_start = db.Column(db.DateTime, default=datetime.utcnow)
    cycle_end = db.Column(db.DateTime)
    
    last_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "ticker": self.ticker,
            "name": self.name,
            "shares": self.shares,
            "pool": self.pool,
            "v_value": self.v_value,
            "vr_type": self.vr_type,
            "g_value": self.g_value,
            "band_ratio": self.band_ratio,
            "pool_limit": self.pool_limit,
            "monthly_extra": self.monthly_extra,
            "cycle_start": self.cycle_start.strftime('%Y-%m-%d') if self.cycle_start else None,
            "cycle_end": self.cycle_end.strftime('%Y-%m-%d') if self.cycle_end else None
        }

class LedgerTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False) # e.g. 2026-06-17
    time = db.Column(db.String(20)) # e.g. 14:27:19
    tx_type = db.Column(db.String(20)) # 지출, 수입, 이체
    main_category = db.Column(db.String(50))
    sub_category = db.Column(db.String(50))
    description = db.Column(db.String(255))
    amount = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(10), default='KRW')
    payment_method = db.Column(db.String(100))
    memo = db.Column(db.Text)
    
    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date,
            "time": self.time,
            "tx_type": self.tx_type,
            "main_category": self.main_category,
            "sub_category": self.sub_category,
            "description": self.description,
            "amount": self.amount,
            "currency": self.currency,
            "payment_method": self.payment_method,
            "memo": self.memo
        }

class AssetStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50)) # e.g., '투자', '부동산', '계좌', '총계'
    institution = db.Column(db.String(100)) # e.g., '토스증권'
    name = db.Column(db.String(100)) # e.g., 'DIVO', '총자산'
    principal = db.Column(db.Float, default=0.0) # 투자원금
    value = db.Column(db.Float, default=0.0) # 평가금액
    return_rate = db.Column(db.Float, default=0.0) # 수익률
    
    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "institution": self.institution,
            "name": self.name,
            "principal": self.principal,
            "value": self.value,
            "return_rate": self.return_rate
        }

class NetWorthSnapshot(db.Model):
    """Records the actual net worth at each Excel upload point."""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False, unique=True)  # e.g. 2026-06-18
    net_worth = db.Column(db.Float, default=0.0)
    total_assets = db.Column(db.Float, default=0.0)
    total_debt = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date,
            "net_worth": self.net_worth,
            "total_assets": self.total_assets,
            "total_debt": self.total_debt,
        }
