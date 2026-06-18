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
