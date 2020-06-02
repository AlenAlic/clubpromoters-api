from ext import db
from models.tables import TABLE_REFUND, TABLE_PURCHASE
from models import TrackModifications
from datetime import datetime
from utilities import datetime_browser


class Refund(db.Model, TrackModifications):
    __tablename__ = TABLE_REFUND
    refund_id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer, nullable=False, default=0)
    refund_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    purchase_id = db.Column(db.Integer, db.ForeignKey(f"{TABLE_PURCHASE}.purchase_id"))
    purchase = db.relationship('Purchase', back_populates='refunds', single_parent=True)
    mollie_refund_id = db.Column(db.String(128), nullable=False, default="")

    def __repr__(self):
        return f"{self.refund_id}: {self.mollie_refund_id}"

    def set_price(self, price_float):
        self.price = int(price_float * 100)

    def get_price(self):
        return float(self.price)/100

    def json(self):
        return {
            "refund_id": self.refund_id,
            "price": self.get_price(),
            "mollie_refund_id": self.mollie_refund_id,
            "date": datetime_browser(self.refund_datetime),
        }
