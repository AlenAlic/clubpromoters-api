from ext import db
from models.tables import TABLE_PURCHASE, TABLE_PARTY, TABLE_CODE, TABLE_USERS
from models import TrackModifications
from flask import current_app
from flask_login import current_user
from datetime import datetime
from constants.mollie import STATUS_OPEN, STATUS_PENDING, STATUS_PAID, STATUS_CANCELED
from utilities import datetime_browser
from hashlib import sha3_256
import pyqrcode
from io import BytesIO
from models.configuration import config


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
    promoter_commission = db.Column(db.Integer, nullable=False, default=15)
    club_owner_commission = db.Column(db.Integer, nullable=False, default=10)
    administration_costs = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"Purchase {self.purchase_id} - Party: {self.party} - Tickets: {len(self.tickets)}"

    def set_ticket_price(self, price_float):
        self.ticket_price = int(float(price_float) * 100)

    def get_ticket_price(self):
        return float(self.ticket_price)/100

    def set_administration_costs(self, price_float):
        self.administration_costs = int(float(price_float) * 100)

    def get_administration_costs(self):
        return float(self.administration_costs)/100

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    def set_commissions(self):
        self.promoter_commission = max(self.party.promoter_commission, self.promoter.commission)
        self.club_owner_commission = min(self.party.club_owner_commission, self.party.club_owner.commission)

    def set_price(self, price_float):
        self.price = int(price_float * 100)

    def get_price(self):
        return float(self.price)/100

    @property
    def number_of_tickets(self):
        return len(self.tickets)

    def mollie_description(self):
        return f"{len(self.tickets)} tickets to {self.party}"

    def mollie_price(self):
        return '{:,.2f}'.format(self.get_price() + self.get_administration_costs())

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
            "name": self.full_name,
            "email": self.email,
            "number_of_tickets": self.number_of_tickets,
            "ticket_price": self.get_ticket_price(),
            "party": {
                "id": self.party.party_id,
                "club": self.party.club_owner.club,
                "name": self.party.name,
                "start_date": datetime_browser(self.party.party_start_datetime),
                "end_date": datetime_browser(self.party.party_end_datetime),
            },
            "administration_costs": self.administration_costs,
        }
        if current_user.is_organizer:
            data.update({
                "entrance_code": self.entrance_code(),
                "purchase_date": datetime_browser(self.purchase_datetime),
                "price": self.get_price(),
                "refunds": [r.json() for r in self.refunds],
                "status": self.status,
                "mollie_payment_id": self.mollie_payment_id,
                "mollie_description": self.mollie_description(),
            })
        if current_user.is_hostess:
            data.update({
                "entrance_code": self.entrance_code(),
                "paid": self.status == STATUS_PAID,
                "tickets": [t.json() for t in self.tickets],
                "available": len([t for t in self.tickets if t.available()]) > 0,
            })
        return data

    def num_tickets(self):
        return len(self.tickets) if self.status == STATUS_PAID else 0

    # PromoterFinances
    def promoter_tickets(self):
        return len(self.tickets)

    def promoter_price(self):
        if self.status == STATUS_PAID:
            minimum_promoter_commission = max(
                self.promoter.minimum_promoter_commission,
                config().minimum_promoter_commission
            ) * self.number_of_tickets
            return max(self.get_price() * self.promoter_commission, minimum_promoter_commission) / 100
        else:
            return 0

    def num_refunded_tickets(self):
        return len([t for t in self.tickets if t.refunded])

    def refunded_price(self):
        return self.get_ticket_price() * self.num_refunded_tickets() * self.promoter_commission / 100

    def promoter_finances(self):
        return {
            "tickets": self.num_tickets(),
            "promoter_price": self.promoter_price(),
            "refunded_price": self.refunded_price()
        }

    # ClubOwnerFinances
    def club_owner_price(self):
        if self.status == STATUS_PAID:
            return max(self.get_price() * self.club_owner_commission, config().minimum_promoter_commission) / 100
        else:
            return 0

    def club_owner_refunded_price(self):
        return self.get_ticket_price() * self.num_refunded_tickets() * self.promoter_commission / 100

    def club_owner_finances(self):
        return {
            "tickets": self.num_tickets(),
            "promoter_price": self.club_owner_price(),
            "refunded_price": self.club_owner_refunded_price()
        }

    # PastParties
    def get_price_with_refunds(self):
        return self.get_price() - self.purchase_refund()

    def purchase_refund(self):
        return sum([r.get_price() for r in self.refunds])

    def purchase_promoter_cut(self):
        return self.get_price() * self.promoter_commission / 100

    def purchase_club_owner_cut(self):
        return self.get_price_with_refunds() * self.club_owner_commission / 100

    def purchase_date(self):
        return self.purchase_datetime.strftime("%d-%m-%Y %H:%M")
