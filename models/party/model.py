from ext import db
from models.tables import TABLE_PARTY, TABLE_LOCATION, TABLE_USERS, TABLE_FILE, TABLE_PARTY_FILES
from models import TrackModifications
from flask_login import current_user
from datetime import datetime, timedelta
from sqlalchemy.ext.associationproxy import association_proxy
from constants.mollie import STATUS_OPEN, STATUS_PENDING, STATUS_PAID
from utilities import datetime_browser
from .constants import NORMAL


class Party(db.Model, TrackModifications):
    __tablename__ = TABLE_PARTY
    party_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey(f"{TABLE_LOCATION}.location_id"))
    location = db.relationship('Location', back_populates='parties')
    is_active = db.Column(db.Boolean, index=True, nullable=False, default=False)
    party_start_datetime = db.Column(db.DateTime, default=datetime.utcnow())
    party_end_datetime = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(hours=4))
    status = db.Column(db.String(128), nullable=False, default=NORMAL)
    num_available_tickets = db.Column(db.Integer, nullable=False, default=0)
    ticket_price = db.Column(db.Integer, nullable=False, default=0)
    purchases = db.relationship('Purchase', back_populates='party', cascade='all, delete-orphan')
    club_owner_id = db.Column(db.Integer, db.ForeignKey(f"{TABLE_USERS}.user_id"))
    club_owner = db.relationship('User', back_populates='parties')
    logo_id = db.Column(db.Integer, db.ForeignKey(f"{TABLE_FILE}.file_id"))
    logo = db.relationship("File")
    files = association_proxy(TABLE_PARTY_FILES, 'file')
    club_owner_commission = db.Column(db.Integer, nullable=False, default=10)
    promoter_commission = db.Column(db.Integer, nullable=False, default=15)
    description = db.Column(db.String(1024), nullable=True)
    interval = db.Column(db.Integer, nullable=False, default=200)

    def __repr__(self):
        return f"{self.party_id}"

    def set_ticket_price(self, price_float):
        self.ticket_price = int(float(price_float) * 100)

    def get_ticket_price(self):
        return float(self.ticket_price)/100

    def tickets_with_status(self, status=""):
        return [t for p in self.purchases for t in p.tickets if p.status == status]

    def num_tickets_with_status(self, status=""):
        return len(self.tickets_with_status(status))

    def sold_tickets(self):
        return self.num_tickets_with_status(STATUS_PAID)

    def tickets_on_hold(self):
        return self.num_tickets_with_status(STATUS_PENDING) + self.num_tickets_with_status(STATUS_OPEN)

    def locked_tickets(self):
        return self.sold_tickets() + self.tickets_on_hold()

    def tickets_denied_entry(self):
        return len([t for p in self.purchases for t in p.tickets if t.denied_entry])

    def remaining_tickets(self):
        return self.num_available_tickets - self.locked_tickets()

    def check_ticket_availability(self, requested_tickets):
        return self.remaining_tickets() >= requested_tickets

    def party_date(self):
        return self.party_start_datetime.strftime("%d %B, %Y")

    def party_time(self):
        return f'{self.party_start_datetime.strftime("%H:%M")} - {self.party_end_datetime.strftime("%H:%M")}'

    def json(self):
        files = sorted([party_file for party_file in self.party_files], key=lambda x: x.order)
        files = [party_file.file for party_file in files]
        data = {
            "id": self.party_id,
            "club": self.club_owner.club,
            "name": self.name,
            "location": self.location.json() if self.location else None,
            "ticket_price": self.get_ticket_price(),
            "num_available_tickets": self.num_available_tickets,
            "start_date": datetime_browser(self.party_start_datetime),
            "end_date": datetime_browser(self.party_end_datetime),
            "club_owner_commission": self.club_owner_commission,
            "promoter_commission": self.promoter_commission,
            "images": [file.json() for file in files if not file.logo],
            "logo": self.logo.json() if self.logo else None,
            "sold_tickets": self.sold_tickets(),
            "tickets_on_hold": self.tickets_on_hold(),
            "locked_tickets": self.locked_tickets(),
            "remaining_tickets": self.remaining_tickets(),
            "tickets_denied_entry": self.tickets_denied_entry(),
            "party_income": self.party_income(),
            "party_refunds": self.party_refunds(),
            "party_promoter_cut": self.party_promoter_cut(),
            "party_club_owner_cut": self.party_club_owner_cut(),
            "party_profit": self.party_profit(),
            "description": self.description,
            "interval": self.interval,
        }
        return data

    def purchases_with_status(self, status=""):
        return [p for p in self.purchases if p.status == status]

    def paid_purchases(self):
        return self.purchases_with_status(STATUS_PAID)

    def party_potential_income(self):
        return sum([p.get_price() for p in self.paid_purchases()])

    def party_tickets_with_potential_refund(self):
        return [t for t in self.tickets_with_status(STATUS_PAID) if t.denied_entry]

    def num_party_tickets_with_potential_refund(self):
        return len(self.party_tickets_with_potential_refund())

    def party_potential_refund(self):
        return sum([t.purchase.get_ticket_price() for t in self.party_tickets_with_potential_refund()])

    def promoter_finances(self, user=current_user):
        return {
            "party_id": self.party_id,
            "club": self.club_owner.club,
            "location": self.location.json(),
            "start_date": datetime_browser(self.party_start_datetime),
            "ticket_price": self.get_ticket_price(),
            "tickets": sum([p.num_tickets() for p in self.purchases if p.promoter == user]),
            "price": sum([p.promoter_price() for p in self.purchases if p.promoter == user]),
            # "refund_tickets": sum([p.refunded_tickets() for p in self.purchases if p.promoter == user]),
            # "refund_price": sum([p.refunded_price() for p in self.purchases if p.promoter == user])
        }

    def club_owner_finances(self):
        return {
            "party_id": self.party_id,
            "club": self.club_owner.club,
            "location": self.location.json(),
            "start_date": datetime_browser(self.party_start_datetime),
            "tickets": sum([p.num_tickets() for p in self.purchases]),
            "price": sum([p.club_owner_price() for p in self.purchases]),
            # "refund_tickets": sum([p.refunded_tickets() for p in self.purchases if p.promoter == user]),
            # "refund_price": sum([p.refunded_price() for p in self.purchases if p.promoter == user])
        }

    # PastParties
    @property
    def paid_purchases(self):
        return [p for p in self.purchases if p.status == STATUS_PAID]

    def party_income(self):
        return sum([p.get_price() for p in self.paid_purchases])

    def party_refunds(self):
        return sum([p.purchase_refund() for p in self.paid_purchases])

    def party_promoter_cut(self):
        return sum([p.purchase_promoter_cut() for p in self.paid_purchases])

    def party_club_owner_cut(self):
        return sum([p.purchase_club_owner_cut() for p in self.paid_purchases])

    def party_profit(self):
        return self.party_income() - self.party_refunds() - self.party_promoter_cut() - self.party_club_owner_cut()
