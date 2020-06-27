from ext import db
from models.tables import TABLE_PURCHASE, TABLE_PARTY, TABLE_CODE, TABLE_USERS
from models import TrackModifications
from flask import current_app, render_template, request
from flask_login import current_user
from datetime import datetime
from constants.mollie import STATUS_OPEN, STATUS_PENDING, STATUS_PAID, STATUS_CANCELED
from utilities import datetime_browser, cents_to_euro
from hashlib import sha3_256
import pyqrcode
from io import BytesIO
from models.configuration import config
from weasyprint import HTML
import os


class Purchase(db.Model, TrackModifications):
    __tablename__ = TABLE_PURCHASE
    purchase_id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(128), nullable=False, default=STATUS_OPEN)
    first_name = db.Column(db.String(128), nullable=False)
    last_name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), index=True, nullable=False)
    hash = db.Column(db.String(160), nullable=False, default="")
    mollie_payment_id = db.Column(db.String(128), nullable=False, default="")
    purchase_datetime = db.Column(db.DateTime, default=datetime.utcnow())
    ticket_price = db.Column(db.Integer, nullable=False, default=0)
    party_id = db.Column(db.Integer, db.ForeignKey(f"{TABLE_PARTY}.party_id"))
    party = db.relationship('Party', back_populates='purchases', single_parent=True)
    tickets = db.relationship('Ticket', back_populates='purchase', cascade='all, delete-orphan')
    refunds = db.relationship('Refund', back_populates='purchase', cascade='all, delete-orphan')
    code_id = db.Column(db.Integer, db.ForeignKey(f"{TABLE_CODE}.code_id"))
    code = db.relationship('Code', back_populates='purchases')
    promoter_id = db.Column(db.Integer, db.ForeignKey(f"{TABLE_USERS}.user_id"))
    promoter = db.relationship('User', back_populates='purchases')
    promoter_commission = db.Column(db.Integer, nullable=False, default=0)
    club_owner_commission = db.Column(db.Integer, nullable=False, default=0)
    administration_costs = db.Column(db.Integer, nullable=False, default=0)
    vat_percentage = db.Column(db.Integer, nullable=False, default=9)
    receipt_path = db.Column(db.String(512), nullable=True)
    tickets_path = db.Column(db.String(512), nullable=True)
    minimum_promoter_commission = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"Purchase {self.purchase_id} - Party: {self.party} - Tickets: {len(self.tickets)}"

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    def set_commissions(self):
        self.promoter_commission = max(self.party.promoter_commission, self.promoter.commission)
        self.club_owner_commission = min(self.party.club_owner_commission, self.party.club_owner.commission)

    @property
    def number_of_tickets(self):
        return len(self.tickets)

    @property
    def number_of_sold_tickets(self):
        return len([t for t in self.tickets if not t.refunded])

    @property
    def number_of_refunded_tickets(self):
        return len([t for t in self.tickets if t.refunded])

    def mollie_description(self):
        return f"{len(self.tickets)} tickets to {self.party.name}"

    def mollie_price(self):
        return '{:,.2f}'.format(cents_to_euro(self.price + self.administration_costs))

    def set_hash(self):
        purchase_hash = self.calculate_hash()
        while Purchase.query.filter(Purchase.hash == purchase_hash).first() is not None:
            purchase_hash = self.calculate_hash(add_date=True)
        self.hash = purchase_hash
        return self.hash

    def calculate_hash(self, add_date=False):
        purchase_hash = f"Purchase {self.purchase_id} - Party: {self.party} - Email: {self.email} - " \
            f"{current_app.config.get('SECRET_KEY')}{datetime.utcnow() if add_date else ''}"
        return sha3_256(purchase_hash.encode()).hexdigest()

    def purchase_paid(self):
        self.status = STATUS_PAID

    def purchase_pending(self):
        self.status = STATUS_PENDING

    def cancel_purchase(self):
        self.status = STATUS_CANCELED

    def qr_code_image(self):
        url = pyqrcode.create(self.hash)
        img = BytesIO()
        url.png(img, scale=6)
        return img.getvalue()

    def entrance_code(self):
        return f"{ self.party_id }-{ self.purchase_id }"

    def json(self):
        data = {
            "id": self.purchase_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "email": self.email,
            "number_of_tickets": self.number_of_tickets,
            "ticket_price": cents_to_euro(self.ticket_price),
            "party": {
                "id": self.party.party_id,
                "club": self.party.club_owner.club,
                "name": self.party.name,
                "start_date": datetime_browser(self.party.party_start_datetime),
                "end_date": datetime_browser(self.party.party_end_datetime),
            },
            "administration_costs": cents_to_euro(self.administration_costs),
        }
        if current_user.is_organizer:
            data.update({
                "entrance_code": self.entrance_code(),
                "purchase_date": datetime_browser(self.purchase_datetime),
                "price": cents_to_euro(self.price),
                "refunds": [r.json() for r in self.refunds],
                "status": self.status,
                "mollie_payment_id": self.mollie_payment_id,
                "mollie_description": self.mollie_description(),
                "tickets": [t.json() for t in self.tickets],
            })
        if current_user.is_hostess:
            data.update({
                "entrance_code": self.entrance_code(),
                "paid": self.status == STATUS_PAID,
                "tickets": [t.json() for t in self.tickets],
                "available": len([t for t in self.tickets if t.is_available]) > 0,
            })
        return data

    @property
    def refunded_amount(self):
        return sum([r.price for r in self.refunds])

    @property
    def receipt_file_name(self):
        return f"receipt.{self.purchase_id}.{self.receipt_number}.{self.receipt_reference}.pdf"

    def generate_receipt(self):
        conf = config()
        path = os.path.join(current_app.receipts_folder, self.receipt_file_name)
        HTML(string=render_template("receipts/receipt_template.html", purchase=self, conf=conf),
             base_url=request.base_url).write_pdf(path)
        self.receipt_path = path

    @property
    def receipts_file_exists(self):
        return os.path.exists(self.receipt_path)

    @property
    def receipt_number(self):
        n = f"{self.purchase_id}"
        return f"{self.purchase_datetime.strftime('%Y%m')}{n.zfill(6)}"

    @property
    def receipt_reference(self):
        return self.mollie_payment_id.replace("tr_", "")

    @property
    def receipt_ticket_price_no_vat(self):
        return int(self.ticket_price * 100 / (self.vat_percentage + 100))

    @property
    def receipt_price_no_vat(self):
        return self.receipt_ticket_price_no_vat * self.number_of_tickets

    @property
    def administration_costs_no_vat(self):
        return int(self.administration_costs * 100 / (self.vat_percentage + 100))

    @property
    def vat(self):
        return self.price - self.receipt_price_no_vat + \
               self.administration_costs - self.administration_costs_no_vat

    @property
    def tickets_file_name(self):
        return f"tickets.{self.purchase_id}.{self.receipt_number}.{self.receipt_reference}.pdf"

    def generate_tickets(self):
        conf = config()
        path = os.path.join(current_app.tickets_folder, self.tickets_file_name)
        HTML(string=render_template("tickets/ticket_template.html", purchase=self, conf=conf),
             base_url=request.base_url).write_pdf(path)
        self.tickets_path = path

    @property
    def tickets_file_exists(self):
        return os.path.exists(self.tickets_path)

    # Organizer
    @property
    def expenses_promoter_commissions(self):
        if self.status == STATUS_PAID:
            return max([int(self.ticket_price * self.promoter_commission / 100), self.minimum_promoter_commission])\
                   * self.number_of_sold_tickets
        return 0

    @property
    def expenses_club_owner_commissions(self):
        if self.status == STATUS_PAID:
            return int((self.price - self.refunded_amount) * self.club_owner_commission / 100)
        return 0

    # Promoter
    @property
    def income_promoter_commissions(self):
        return self.expenses_promoter_commissions

    # Club Owner
    @property
    def income_club_owner_commissions(self):
        return self.expenses_club_owner_commissions

