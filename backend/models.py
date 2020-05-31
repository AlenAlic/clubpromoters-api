from backend import db, login, Anonymous
from flask import current_app, request, g
from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from backend.values import *
from time import time
import jwt
from datetime import datetime, timedelta
from functools import wraps
from hashlib import sha3_256
import pyqrcode
import urllib.parse
from io import BytesIO
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func


def datetime_browser(dt):
    return dt.strftime(DATETIME_FORMAT)


def format_euro(price):
    if price > 0:
        p = '€{:,.2f}'.format(price)
        p = p.replace(".00", "")
        return p
    else:
        return '€0'


# Table names
USERS = 'users'
LOCATION = "location"
CONFIGURATION = 'configuration'
PARTY = 'party'
TICKET = 'ticket'
PURCHASE = 'purchase'
REFUND = 'refund'
CODE = 'code'
FILE = 'file'
TABLE_PARTY_FILES = 'party_files'


def requires_access_level(access_levels):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.access not in access_levels:
                return UNAUTHORIZED
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def code_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        code = get_code_from_request(request)
        if code is None:
            return PRECONDITION_REQUIRED
        return view(**kwargs)
    return wrapped_view


class TrackModifications(object):
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def get_token_from_request(req):
    token = req.headers.get("Authorization").replace("Bearer ", "")
    return jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])


def get_code_from_request(req):
    code = req.headers.get("Code")
    return Code.query.filter(Code.active.is_(True), Code.code == code).first()


@login.request_loader
def load_user(req):
    try:
        data = get_token_from_request(req)
        user_id = data["id"]
        reset_index = data["reset_index"]
    except (jwt.exceptions.InvalidTokenError, AttributeError, KeyError):
        return None
    user = User.query.filter(User.user_id == user_id, User.reset_index == reset_index).first()
    return user if user is not None else None


class User(UserMixin, Anonymous, db.Model, TrackModifications):
    __tablename__ = USERS
    user_id = db.Column(db.Integer, primary_key=True)
    reset_index = db.Column(db.Integer, nullable=False, default=0)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    access = db.Column(db.Integer, index=True, nullable=False)
    is_active = db.Column(db.Boolean, index=True, nullable=False, default=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    auth_code = db.Column(db.String(128), nullable=True)
    club = db.Column(db.String(256), nullable=True)
    first_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    code = db.relationship('Code', back_populates='user', uselist=False)
    club_owner_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    hostesses = db.relationship("User", backref=db.backref('club_owner', remote_side=[user_id]))
    parties = db.relationship('Party', back_populates='club_owner')
    purchases = db.relationship('Purchase', back_populates='promoter')
    commission = db.Column(db.Integer, nullable=False, default=0)
    working = db.Column(db.Boolean, nullable=True, default=False)
    files = db.relationship("File", back_populates='user')
    locations = db.relationship("Location", back_populates='user')
    minimum_promoter_commission = db.Column(db.Integer, nullable=False, default=100)
    iban = db.Column(db.String(30), nullable=True)
    iban_verified = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f'{self.email}'

    def get_id(self):
        return f"{self.user_id}-{self.reset_index}"

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def is_admin(self):
        return self.access == AL_ADMIN

    def is_organizer(self):
        return self.access == AL_ORGANIZER

    def is_club_owner(self):
        return self.access == AL_CLUB_OWNER

    def is_promoter(self):
        return self.access == AL_PROMOTER

    def is_hostess(self):
        return self.access == AL_HOSTESS

    def allowed(self, access_levels):
        return self.access in access_levels

    def set_password(self, password, increment=True):
        self.password_hash = generate_password_hash(password)
        if self.reset_index is not None and increment:
            self.reset_index += 1
        db.session.commit()

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=SECONDS_QUARTER):
        return jwt.encode({'reset_password': self.user_id, 'exp': time() + expires_in},
                          current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            user_id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except jwt.exceptions.InvalidTokenError:
            return False
        return User.query.get(user_id)

    def get_auth_token(self, expires_in=SECONDS_DAY):
        return jwt.encode({
            'id': self.user_id,
            "reset_index": self.reset_index,
            "email": self.email,
            "access": self.access,
            "first_name": self.first_name,
            "last_name": self.last_name,
            'iat': time(),
            'exp': time() + expires_in,
            }, current_app.config['SECRET_KEY'],  algorithm='HS256').decode('utf-8')

    def profile(self):
        if current_user == self:
            data = {
                "id": self.user_id,
                "first_name": self.first_name,
                "last_name": self.last_name,
                "email": self.email,
            }
            if self.is_club_owner():
                data.update({
                    "club": self.club,
                    "commission": self.commission,
                    "iban": self.iban,
                })
            if self.is_promoter():
                data.update({
                    "code": self.code.json() if self.code else None,
                    "commission": self.commission,
                    "iban": self.iban,
                })
            return data
        return None

    def assets(self):
        return {
            "images": [file.json() for file in self.files if not file.logo],
            "logos": [file.json() for file in self.files if file.logo],
        }

    def json(self):
        data = {
            'id': self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "name": self.full_name(),
            "email": self.email,
            "access": self.access,
            "is_active": self.is_active,
            "last_seen": self.last_seen,
            "locations": [loc.json() for loc in self.locations]
        }
        if self.is_club_owner():
            data.update({
                "hostesses": [{
                    "id": h.user_id,
                    "email": h.email,
                    "name": h.full_name(),
                    "last_seen": h.last_seen,
                    "is_active": h.is_active,
                } for h in self.hostesses],
                "commission": self.commission,
                "club": self.club,
            })
        if self.is_promoter():
            data.update({
                "commission": self.commission,
            })
            if self.code is not None:
                data.update({
                    "code": self.code.json(),
                })
        if self.is_hostess():
            data.update({
                "working": self.working,
            })
        return data

    def commissions_json(self, purchases):
        data = {
            'id': self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "name": self.full_name(),
            "email": self.email,
            "access": self.access,
            "is_active": self.is_active,
            "last_seen": self.last_seen,
        }
        total = 0
        if self.is_promoter():
            purchases = [p for p in purchases if p.promoter == self and p.status == STATUS_PAID]
            total = sum([p.promoter_price() for p in purchases])
            parties = Party.query.filter(Party.party_id.in_([p.party_id for p in purchases if p.promoter == self])) \
                .order_by(Party.party_start_datetime).all()
            data.update({
                "parties": [p.promoter_finances(self) for p in parties]
            })
        if self.is_club_owner():
            purchases = [p for p in purchases if p.party.club_owner == self and p.status == STATUS_PAID]
            total = sum([p.club_owner_price() for p in purchases])
            parties = Party.query.filter(Party.party_id.in_([p.party_id for p in purchases])) \
                .order_by(Party.party_start_datetime).all()
            data.update({
                "club": self.club,
                "parties": [p.club_owner_finances() for p in parties],
            })
        data.update({
            "total": total,
        })
        return data

    def promoter_income(self, month):
        purchases = Purchase.query.filter(Purchase.purchase_datetime < datetime.now(),
                                          func.month(Purchase.purchase_datetime) == func.month(month),
                                          func.year(Purchase.purchase_datetime) == func.year(month),
                                          Purchase.promoter_id == self.user_id,
                                          Purchase.status == STATUS_PAID).all()
        total = sum([p.promoter_price() for p in purchases])
        parties = Party.query.filter(Party.party_id.in_([p.party_id for p in purchases if p.promoter == self])) \
            .order_by(Party.party_start_datetime).all()
        data = {
            "parties": [p.promoter_finances(self) for p in parties],
            "total": total,
        }
        return data


class Location(db.Model, TrackModifications):
    __tablename__ = LOCATION
    location_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    street = db.Column(db.String(256), nullable=False)
    street_number = db.Column(db.String(12), nullable=False)
    street_number_addition = db.Column(db.String(12))
    postal_code = db.Column(db.Integer(), nullable=False)
    postal_code_letters = db.Column(db.String(2), nullable=False)
    city = db.Column(db.String(256), nullable=False)
    maps_url = db.Column(db.String(512))
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    user = db.relationship('User', back_populates='locations')
    parties = db.relationship('Party', back_populates='location')

    def __repr__(self):
        return f"{self.location_id}: {self.name}"

    def json(self):
        data = {
            "id": self.location_id,
            "name": self.name,
            "street": self.street,
            "street_number": self.street_number,
            "street_number_addition": self.street_number_addition,
            "postal_code": self.postal_code,
            "postal_code_letters": self.postal_code_letters,
            "city": self.city,
            "maps_url": self.maps_url,
            "user_id": self.user_id,
        }
        return data


class Configuration(db.Model, TrackModifications):
    __tablename__ = CONFIGURATION
    lock_id = db.Column(db.Integer, primary_key=True)
    mollie_api_key = db.Column(db.String(128))
    allowed_image_types = db.Column(db.String(256), nullable=False,
                                    default="jpg,jpeg,png", server_default="jpg,jpeg,png")
    default_club_owner_commission = db.Column(db.Integer, nullable=False, default=10)
    default_promoter_commission = db.Column(db.Integer, nullable=False, default=15)
    site_available = db.Column(db.Boolean, nullable=False, default=False)
    test_email = db.Column(db.String(128))
    terms_id = db.Column(db.Integer, db.ForeignKey(f"{FILE}.file_id"))
    terms = db.relationship("File")
    minimum_promoter_commission = db.Column(db.Integer, nullable=False, default=100)
    administration_costs = db.Column(db.Integer, nullable=False, default=0)

    def allowed_file_types(self):
        return self.allowed_image_types.split(",")

    def get_minimum_promoter_commission(self):
        return float(self.minimum_promoter_commission)/100

    def set_minimum_promoter_commission(self, price_float):
        self.minimum_promoter_commission = int(float(price_float) * 100)

    def get_administration_costs(self):
        return float(self.administration_costs)/100

    def set_administration_costs(self, price_float):
        self.administration_costs = int(float(price_float) * 100)

    def json(self):
        return {
            "default_club_owner_commission": self.default_club_owner_commission,
            "default_promoter_commission": self.default_promoter_commission,
            "mollie_api_key": self.mollie_api_key,
            "test_email": self.test_email,
            "terms": self.terms.url() if self.terms else None,
            "minimum_promoter_commission": self.get_minimum_promoter_commission(),
            "administration_costs": self.get_administration_costs(),
        }


class PartyFile(db.Model):
    __tablename__ = TABLE_PARTY_FILES
    party_id = db.Column(db.Integer, db.ForeignKey(f'{PARTY}.party_id', onupdate="CASCADE", ondelete="CASCADE"),
                         primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey(f'{FILE}.file_id', onupdate="CASCADE", ondelete="CASCADE"),
                        primary_key=True)
    party = db.relationship("Party", backref=db.backref("party_files", cascade="all, delete-orphan"))
    file = db.relationship("File")
    order = db.Column(db.Integer, nullable=False)
    __table_args__ = (db.UniqueConstraint('party_id', 'file_id', name='_party_file_uc'),)


class Party(db.Model, TrackModifications):
    __tablename__ = PARTY
    party_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey(f"{LOCATION}.location_id"))
    location = db.relationship('Location', back_populates='parties')
    is_active = db.Column(db.Boolean, index=True, nullable=False, default=False)
    party_start_datetime = db.Column(db.DateTime, default=datetime.utcnow())
    party_end_datetime = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(hours=4))
    status = db.Column(db.String(128), nullable=False, default=NORMAL)
    num_available_tickets = db.Column(db.Integer, nullable=False, default=0)
    ticket_price = db.Column(db.Integer, nullable=False, default=0)
    purchases = db.relationship('Purchase', back_populates='party', cascade='all, delete-orphan')
    club_owner_id = db.Column(db.Integer, db.ForeignKey(f"{USERS}.user_id"))
    club_owner = db.relationship('User', back_populates='parties')
    logo_id = db.Column(db.Integer, db.ForeignKey(f"{FILE}.file_id"))
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
    def party_income(self):
        return sum([p.get_price() for p in self.purchases])

    def party_refunds(self):
        return sum([p.purchase_refund() for p in self.purchases])

    def party_promoter_cut(self):
        return sum([p.purchase_promoter_cut() for p in self.purchases])

    def party_club_owner_cut(self):
        return sum([p.purchase_club_owner_cut() for p in self.purchases])

    def party_profit(self):
        return self.party_income() - self.party_refunds() - self.party_promoter_cut() - self.party_club_owner_cut()


class Ticket(db.Model, TrackModifications):
    __tablename__ = TICKET
    ticket_id = db.Column(db.Integer, primary_key=True)
    used = db.Column(db.Boolean, index=True, nullable=False, default=False)
    denied_entry = db.Column(db.Boolean, index=True, nullable=False, default=False)
    number = db.Column(db.Integer, nullable=False, default=0)
    refunded = db.Column(db.Boolean, nullable=False, default=False)
    purchase_id = db.Column(db.Integer, db.ForeignKey(f"{PURCHASE}.purchase_id"))
    purchase = db.relationship('Purchase', back_populates='tickets', single_parent=True)

    def __repr__(self):
        return f"{self.ticket_id}"

    def available(self):
        return not self.used and not self.denied_entry

    def json(self):
        data = {
            "id": self.ticket_id,
            "used": self.used,
            "denied_entry": self.denied_entry,
            "available": self.available(),
            "number": self.number,
            "refunded": self.refunded,
        }
        return data


class Purchase(db.Model, TrackModifications):
    __tablename__ = PURCHASE
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
    party_id = db.Column(db.Integer, db.ForeignKey(f"{PARTY}.party_id"))
    party = db.relationship('Party', back_populates='purchases', single_parent=True)
    tickets = db.relationship('Ticket', back_populates='purchase', cascade='all, delete-orphan')
    refunds = db.relationship('Refund', back_populates='purchase', cascade='all, delete-orphan')
    code_id = db.Column(db.Integer, db.ForeignKey(f"{CODE}.code_id"))
    code = db.relationship('Code', back_populates='purchases')
    promoter_id = db.Column(db.Integer, db.ForeignKey(f"{USERS}.user_id"))
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

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

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
            "name": self.full_name(),
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
        if current_user.is_organizer():
            data.update({
                "entrance_code": self.entrance_code(),
                "purchase_date": datetime_browser(self.purchase_datetime),
                "price": self.get_price(),
                "refunds": [r.json() for r in self.refunds],
                "status": self.status,
                "mollie_payment_id": self.mollie_payment_id,
                "mollie_description": self.mollie_description(),
            })
        if current_user.is_hostess():
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
                g.config.minimum_promoter_commission
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
            return max(self.get_price() * self.club_owner_commission, g.config.minimum_promoter_commission) / 100
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


class Refund(db.Model, TrackModifications):
    __tablename__ = REFUND
    refund_id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer, nullable=False, default=0)
    refund_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    purchase_id = db.Column(db.Integer, db.ForeignKey(f"{PURCHASE}.purchase_id"))
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


class Code(db.Model, TrackModifications):
    __tablename__ = CODE
    code_id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey(f"{USERS}.user_id"))
    user = db.relationship('User', back_populates='code', single_parent=True)
    purchases = db.relationship('Purchase', back_populates='code')

    def __repr__(self):
        return self.code

    def deactivate(self):
        self.active = False
        self.user_id = None

    def qr_code(self):
        url = pyqrcode.create(f"{current_app.config.get('BASE_URL')}?code={self.code}")
        return url.png_as_base64_str(scale=10)

    def json(self):
        data = {
            "id": self.code_id,
            "code": self.code,
            "active": self.active,
        }
        if current_user.is_promoter():
            data.update({
                "qr_code": self.qr_code(),
            })
        if self.user_id is not None:
            data["promoter"] = {
                "id": self.user.user_id,
                "name": self.user.full_name()
            }
        return data


class File(db.Model, TrackModifications):
    __tablename__ = FILE
    file_id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(256), nullable=False)
    logo = db.Column(db.Boolean, nullable=False, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    user = db.relationship('User', back_populates='files')

    def __repr__(self):
        return f"{self.file_id}: {self.name}"

    @property
    def directory(self):
        return self.path.rsplit("\\", 1)[0].replace('\\', '/')

    @property
    def filename(self):
        return self.path.rsplit("\\", 1)[1].replace('\\', '/')

    def url(self):
        relative_url = "{static}{file}"\
            .format(static=current_app.static_url_path, file=self.path.split("static")[1].replace('\\', '/'))
        url = f"{request.scheme}://{request.host}{relative_url}"
        return urllib.parse.quote(url, safe="/:")

    def json(self):
        data = {
            "id": self.file_id,
            "url": self.url(),
            "name": self.name,
            "logo": self.logo,
            "user_id": self.user_id,
        }
        return data
