from ext import db
from models.tables import TABLE_PARTY, TABLE_LOCATION, TABLE_USERS, TABLE_FILE, TABLE_PARTY_FILES, TABLE_PARTY_INVOICE
from models import TrackModifications
from flask_login import current_user
from datetime import datetime, timedelta
from sqlalchemy.ext.associationproxy import association_proxy
from constants.mollie import STATUS_OPEN, STATUS_PENDING, STATUS_PAID
from utilities import datetime_browser, cents_to_euro
from .constants import NORMAL
import locale


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
    invoices = db.relationship("Invoice", secondary=TABLE_PARTY_INVOICE)

    def __repr__(self):
        return f"{self.party_id}: {self.club_owner.club}  -  {self.party_start_datetime}"

    def tickets_with_status(self, status=""):
        return [t for p in self.purchases for t in p.tickets if p.status == status]

    def num_tickets_with_status(self, status=""):
        return len(self.tickets_with_status(status))

    def sold_tickets(self):
        return self.tickets_with_status(STATUS_PAID)

    def tickets_on_hold(self):
        return self.tickets_with_status(STATUS_PENDING) + self.tickets_with_status(STATUS_OPEN)

    def locked_tickets(self):
        return self.sold_tickets() + self.tickets_on_hold()

    def tickets_denied_entry(self):
        return [t for p in self.purchases for t in p.tickets if t.denied_entry]

    def tickets_refunded(self):
        return [t for p in self.purchases for t in p.tickets if t.refunded]

    @property
    def num_remaining_tickets(self):
        return self.num_available_tickets - len(self.locked_tickets())

    def check_ticket_availability(self, requested_tickets):
        return self.num_remaining_tickets >= requested_tickets

    def json(self):
        files = sorted([party_file for party_file in self.party_files], key=lambda x: x.order)
        files = [party_file.file for party_file in files]
        data = {
            "id": self.party_id,
            "club": self.club_owner.club,
            "name": self.name,
            "is_active": self.is_active,
            "location": self.location.json() if self.location else None,
            "description": self.description,
            "ticket_price": cents_to_euro(self.ticket_price),
            "num_available_tickets": self.num_available_tickets,
            "start_date": datetime_browser(self.party_start_datetime),
            "end_date": datetime_browser(self.party_end_datetime),
            "club_owner_commission": self.club_owner_commission,
            "promoter_commission": self.promoter_commission,
            "images": [file.json() for file in files if not file.logo],
            "logo": self.logo.json() if self.logo else None,
            "interval": self.interval,
            "num_sold_tickets": len(self.sold_tickets()),
            "num_tickets_on_hold": len(self.tickets_on_hold()),
            "num_locked_tickets": len(self.locked_tickets()),
            "num_remaining_tickets": self.num_remaining_tickets,
            "num_tickets_denied_entry": len(self.tickets_denied_entry()),
            "num_tickets_refunded": len(self.tickets_refunded()),
        }
        if current_user.is_organizer:
            data.update({
                "income_tickets_sold": cents_to_euro(self.income_tickets_sold),
                "income_administration_costs": cents_to_euro(self.income_administration_costs),
                "expenses_refunds": cents_to_euro(self.expenses_refunds),
                "expenses_promoter_commissions": cents_to_euro(self.expenses_promoter_commissions),
                "expenses_club_owner_commissions": cents_to_euro(self.expenses_club_owner_commissions),
                "total_profit": cents_to_euro(self.total_profit),
            })
        if current_user.is_club_owner:
            data.update({
                "commission": cents_to_euro(self.income_club_owner_commission),
            })
        return data

    def invoice_date(self, language):
        locale.setlocale(locale.LC_ALL, language)
        due_date = self.party_start_datetime.strftime("%d %B %Y")
        locale.setlocale(locale.LC_ALL, 'C')
        return due_date

    def purchases_with_status(self, status=""):
        return [p for p in self.purchases if p.status == status]

    @property
    def paid_purchases(self):
        return self.purchases_with_status(STATUS_PAID)

    def promoter_commissions(self, user):
        data = {
            "id": self.party_id,
            "name": self.name,
            "club": self.club_owner.club,
            "location": self.location.json(),
            "start_date": datetime_browser(self.party_start_datetime),
            "end_date": datetime_browser(self.party_end_datetime),
            "number_of_sold_tickets": sum([
                p.number_of_sold_tickets for p in self.paid_purchases if p.promoter == user
            ]),
            "number_of_refunded_tickets": sum([
                p.number_of_refunded_tickets for p in self.paid_purchases if p.promoter == user
            ]),
            "commission": sum([
                cents_to_euro(p.expenses_promoter_commissions) for p in self.paid_purchases if p.promoter == user
            ]),
        }
        return data

    # Organizer
    @property
    def income_tickets_sold(self):
        return sum([p.price for p in self.paid_purchases])

    @property
    def income_administration_costs(self):
        return sum([p.administration_costs for p in self.paid_purchases])

    @property
    def expenses_refunds(self):
        return sum([p.refunded_amount for p in self.paid_purchases])

    @property
    def expenses_promoter_commissions(self):
        return sum([p.expenses_promoter_commissions for p in self.paid_purchases])

    @property
    def expenses_club_owner_commissions(self):
        return sum([p.expenses_club_owner_commissions for p in self.paid_purchases])

    @property
    def total_profit(self):
        return self.income_tickets_sold + self.income_administration_costs - \
               (self.expenses_refunds + self.expenses_promoter_commissions + self.expenses_club_owner_commissions)

    def has_commission(self, user):
        if user.is_club_owner:
            return self.income_club_owner_commission > 0
        if user.is_promoter:
            return self.income_promoter_commission(user) > 0

    # Promoter
    def promoter_purchases(self, promoter):
        return [p for p in self.purchases if p.promoter == promoter and p.status == STATUS_PAID]

    def income_promoter_commission(self, promoter):
        return sum([p.income_promoter_commissions for p in self.promoter_purchases(promoter)])

    # Club Owner
    @property
    def income_club_owner_commission(self):
        return self.expenses_club_owner_commissions

    @property
    def income_number_tickets_sold(self):
        return len([t for p in self.purchases for t in p.tickets if p.status == STATUS_PAID and not t.refunded])
