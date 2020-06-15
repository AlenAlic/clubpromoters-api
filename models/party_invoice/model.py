from ext import db
from models.tables import TABLE_PARTY_INVOICE, TABLE_PARTY, TABLE_INVOICE
from models import TrackModifications


class PartyInvoice(db.Model, TrackModifications):
    __tablename__ = TABLE_PARTY_INVOICE
    id = db.Column(db.Integer(), primary_key=True)
    party_id = db.Column(db.Integer(), db.ForeignKey(f"{TABLE_PARTY}.party_id", ondelete="CASCADE"))
    invoice_id = db.Column(db.Integer(), db.ForeignKey(f"{TABLE_INVOICE}.invoice_id", ondelete="CASCADE"))
    party = db.relationship("Party")
    invoice = db.relationship("Invoice")

    def __repr__(self):
        return f"{self.party_id}-{self.invoice_id}"
