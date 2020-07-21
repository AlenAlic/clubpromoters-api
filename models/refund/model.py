from ext import db
from models.tables import TABLE_REFUND, TABLE_PURCHASE
from models import TrackModifications
from flask import current_app, render_template, request
from datetime import datetime
from utilities import datetime_browser, cents_to_euro
from models.configuration import config
from weasyprint import HTML
import os


class Refund(db.Model, TrackModifications):
    __tablename__ = TABLE_REFUND
    refund_id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer, nullable=False, default=0)
    refund_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    purchase_id = db.Column(db.Integer, db.ForeignKey(f"{TABLE_PURCHASE}.purchase_id"))
    purchase = db.relationship('Purchase', back_populates='refunds')
    mollie_refund_id = db.Column(db.String(128), nullable=False, default="")
    receipt_path = db.Column(db.String(512), nullable=True, default="")
    refund_number = db.Column(db.Integer, nullable=False, default=1)
    tickets = db.relationship('Ticket', back_populates='refund')

    def __repr__(self):
        return f"{self.refund_id}: {self.mollie_refund_id}"

    def json(self):
        return {
            "refund_id": self.refund_id,
            "price": cents_to_euro(self.price),
            "mollie_refund_id": self.mollie_refund_id,
            "date": datetime_browser(self.refund_datetime),
        }

    @property
    def receipt_reference(self):
        return f"{self.purchase.receipt_reference}-{self.refund_number}"

    @property
    def refund_receipt_file_name(self):
        return f"receipt.{self.purchase_id}.{self.receipt_number}.{self.receipt_reference}.pdf"

    def generate_refund_receipt(self):
        conf = config()
        path = os.path.join(current_app.receipts_folder, self.receipt_file_name)
        HTML(string=render_template("receipts/receipt_template.html", purchase=self.purchase, conf=conf, refund=self),
             base_url=request.base_url).write_pdf(path)
        self.receipt_path = path

    @property
    def receipt_number(self):
        return f"{self.purchase.receipt_number}-{self.refund_number}"

    @property
    def refund_price_no_vat(self):
        return int(self.price * 100 / (self.purchase.vat_percentage + 100))

    @property
    def refund_vat(self):
        return self.price - self.refund_price_no_vat
