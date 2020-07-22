from ext import db
from models.tables import TABLE_TICKET, TABLE_PURCHASE, TABLE_REFUND
from models import TrackModifications


class Ticket(db.Model, TrackModifications):
    __tablename__ = TABLE_TICKET
    ticket_id = db.Column(db.Integer, primary_key=True)
    used = db.Column(db.Boolean, index=True, nullable=False, default=False)
    denied_entry = db.Column(db.Boolean, index=True, nullable=False, default=False)
    number = db.Column(db.Integer, nullable=False, default=0)
    purchase_id = db.Column(db.Integer, db.ForeignKey(f"{TABLE_PURCHASE}.purchase_id"))
    purchase = db.relationship('Purchase', back_populates='tickets')
    refund_id = db.Column(db.Integer, db.ForeignKey(f"{TABLE_REFUND}.refund_id"))
    refund = db.relationship('Refund', back_populates='tickets')

    def __repr__(self):
        return f"{self.ticket_id}"

    @property
    def is_available(self):
        return not self.used and not self.denied_entry

    @property
    def refunded(self):
        return bool(self.refund_id)

    def json(self):
        data = {
            "id": self.ticket_id,
            "used": self.used,
            "denied_entry": self.denied_entry,
            "is_available": self.is_available,
            "number": self.number,
            "refunded": self.refunded,
        }
        return data
