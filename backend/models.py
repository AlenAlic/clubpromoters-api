from backend import db, login, Anonymous
from flask import current_app, url_for
from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from backend.values import *
from time import time
import jwt
from datetime import datetime, timedelta
from functools import wraps
from hashlib import sha3_256
import pyqrcode
import os


# Table names
USERS = 'users'
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
        # if "code" not in session:
        #     flash("Cannot enter page without a valid code.")
        #     return redirect(url_for('main.index'))
        return view(**kwargs)
    return wrapped_view


def page_inactive(view):
    @wraps(view)
    def wrapped_view():
        # flash("Page inactive for testing purchases")
        # return redirect(url_for('main.index'))
        return view
    return wrapped_view


class TrackModifications(object):
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def get_token_from_request(request):
    token = request.headers.get("Authorization").replace("Bearer ", "")
    return jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])


@login.request_loader
def load_user(request):
    try:
        data = get_token_from_request(request)
        user_id = data["id"]
        reset_index = data["reset_index"]
    except (jwt.exceptions.InvalidTokenError, AttributeError, KeyError):
        return None
    user = User.query.filter(User.user_id == user_id, User.reset_index == reset_index).first()
    return user if user is not None else None


class User(UserMixin, Anonymous, db.Model, TrackModifications):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    reset_index = db.Column(db.Integer, nullable=False, default=0)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    access = db.Column(db.Integer, index=True, nullable=False)
    is_active = db.Column(db.Boolean, index=True, nullable=False, default=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    first_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    auth_code = db.Column(db.String(128), nullable=True)
    code = db.relationship('Code', back_populates='user', uselist=False)
    hostess_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    hostesses = db.relationship("User", backref=db.backref('club_owner', remote_side=[user_id]))
    parties = db.relationship('Party', back_populates='club_owner')
    purchases = db.relationship('Purchase', back_populates='promoter')
    commission = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f'{self.email}'

    def get_id(self):
        return f"{self.user_id}-{self.reset_index}"

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
            "first_name": self.first_name,
            "last_name": self.last_name,
            'iat': time(),
            'exp': time() + expires_in,
            }, current_app.config['SECRET_KEY'],  algorithm='HS256').decode('utf-8')

    def profile(self):
        if current_user == self:
            return {
                "id": self.user_id,
                "first_name": self.first_name,
                "last_name": self.last_name,
                "email": self.email,
                "is_active": self.is_active
            }
        return None


class Configuration(db.Model, TrackModifications):
    __tablename__ = CONFIGURATION
    lock_id = db.Column(db.Integer, primary_key=True)
    mollie_api_key = db.Column(db.String(128))
    allowed_image_types = db.Column(db.String(256), nullable=False, default="jpg,jpeg,png", server_default="jpg,jpeg,png")
    default_club_owner_commission = db.Column(db.Integer, nullable=False, default=10)
    default_promoter_commission = db.Column(db.Integer, nullable=False, default=15)
    site_available = db.Column(db.Boolean, nullable=False, default=False)

    def allowed_file_types(self):
        return self.allowed_image_types.split(",")


party_file_table = db.Table(
    TABLE_PARTY_FILES, db.Model.metadata,
    db.Column('party_id', db.Integer,
              db.ForeignKey(f'{PARTY}.party_id', onupdate="CASCADE", ondelete="CASCADE")),
    db.Column('file_id', db.Integer,
              db.ForeignKey(f'{FILE}.file_id', onupdate="CASCADE", ondelete="CASCADE")),
    db.UniqueConstraint('party_id', 'file_id', name='_party_file_uc')
)


class Party(db.Model, TrackModifications):
    __tablename__ = PARTY
    party_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), index=True, nullable=False)
    is_active = db.Column(db.Boolean, index=True, nullable=False, default=False)
    party_start_datetime = db.Column(db.DateTime, default=datetime.utcnow())
    party_end_datetime = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(hours=4))
    status = db.Column(db.String(128), index=True, nullable=False, default=NORMAL)
    num_available_tickets = db.Column(db.Integer, nullable=False, default=0)
    ticket_price = db.Column(db.Integer, nullable=False, default=0)
    purchases = db.relationship('Purchase', back_populates='party', cascade='all, delete-orphan')
    club_owner_id = db.Column(db.Integer, db.ForeignKey(f"{USERS}.user_id"))
    club_owner = db.relationship('User', back_populates='parties')
    logo = db.Column(db.String(256), nullable=False)
    image = db.Column(db.String(256), nullable=False)
    # files = db.relationship('File', back_populates='party')
    files = db.relationship("File", secondary=party_file_table)
    club_owner_commission = db.Column(db.Integer, nullable=False, default=10)

    def __repr__(self):
        return f"{self.title}"

    def set_ticket_price(self, price_float):
        self.ticket_price = int(price_float * 100)

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

    def remaining_tickets(self):
        return self.num_available_tickets - self.sold_tickets() - self.tickets_on_hold()

    def check_ticket_availability(self, requested_tickets):
        return self.remaining_tickets() >= requested_tickets

    def party_date(self):
        return self.party_start_datetime.strftime("%d %B, %Y")

    def party_time(self):
        return f'{self.party_start_datetime.strftime("%H:%M")} - {self.party_end_datetime.strftime("%H:%M")}'

    def json(self):
        return {
            "party_id": self.party_id,
            "title": self.title,
            "ticket_price": self.get_ticket_price(),
            'party_date': self.party_date(),
            'party_time': self.party_time()
        }

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

    def delete_files_from_hard_disk(self):
        self.image = PLACEHOLDER_URL
        self.logo = PLACEHOLDER_URL
        db.session.commit()
        for file in self.files:
            if os.path.isfile(file.path):
                os.remove(file.path)
            db.session.delete(file)
        db.session.commit()

    # PromoterFinances
    def promoter_finances_json(self):
        return {
            "party_id": self.party_id,
            "title": self.title,
            "party_date": self.party_date(),
            "tickets": sum([p.promoter_tickets() for p in self.purchases if p.promoter == current_user]),
            "price": sum([p.promoter_price() for p in self.purchases if p.promoter == current_user]),
            "refund_tickets": sum([p.refunded_tickets() for p in self.purchases if p.promoter == current_user]),
            "refund_price": sum([p.refunded_price() for p in self.purchases if p.promoter == current_user])
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

    def past_party_json(self):
        return {
            "party_id": self.party_id,
            "title": self.title,
            "party_date": self.party_date(),
            "party_time": self.party_time(),
            "num_available_tickets": self.num_available_tickets,
            "sold_tickets": self.sold_tickets(),
            "remaining_tickets": self.remaining_tickets(),
            "party_income": self.party_income(),
            "party_refunds": self.party_refunds(),
            "party_promoter_cut": self.party_promoter_cut(),
            "party_club_owner_cut": self.party_club_owner_cut(),
            "party_profit": self.party_profit()
        }


class Ticket(db.Model, TrackModifications):
    __tablename__ = TICKET
    ticket_id = db.Column(db.Integer, primary_key=True)
    used = db.Column(db.Boolean, index=True, nullable=False, default=False)
    denied_entry = db.Column(db.Boolean, index=True, nullable=False, default=False)
    number = db.Column(db.Integer, nullable=False, default=0)
    refunded = db.Column(db.Boolean, nullable=False, default=False)
    purchase_id = db.Column(db.Integer, db.ForeignKey(f"{PURCHASE}.purchase_id"))
    purchase = db.relationship('Purchase', back_populates='tickets', single_parent=True)


class Purchase(db.Model, TrackModifications):
    __tablename__ = PURCHASE
    purchase_id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(128), nullable=False, default=STATUS_OPEN)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), index=True, nullable=False)
    hash = db.Column(db.String(160), nullable=False, default="")
    mollie_payment_id = db.Column(db.String(128), nullable=False, default="")
    purchase_datetime = db.Column(db.DateTime, default=datetime.utcnow())
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

    def __repr__(self):
        return f"Purchase {self.purchase_id} - Party: {self.party} - Tickets: {len(self.tickets)}"

    def set_price(self, price_float):
        self.price = int(price_float * 100)

    def get_price(self):
        return float(self.price)/100

    def get_ticket_price(self):
        return self.get_price()/len(self.tickets)

    def mollie_description(self):
        return f"{len(self.tickets)} tickets to {self.party}"

    def mollie_price(self):
        return '{:,.2f}'.format(self.get_price())

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

    def first_name(self):
        return self.name.split(" ")[0]

    def qr_code(self):
        url = pyqrcode.create(self.hash)
        return url.png_as_base64_str(scale=6)

    def entrance_code(self):
        return f"{ self.name }-{ self.purchase_id }".replace(" ", "")

    # PromoterFinances
    def promoter_tickets(self):
        return len(self.tickets)

    def promoter_price(self):
        return self.get_price() * self.promoter_commission / 100

    def refunded_tickets(self):
        return len([t for t in self.tickets if t.refunded])

    def refunded_price(self):
        return self.get_ticket_price() * self.refunded_tickets() * self.promoter_commission / 100

    def promoter_finances_json(self):
        return {
            "tickets": self.promoter_tickets(),
            "promoter_price": self.promoter_price(),
            "refunded_price": self.refunded_price()
        }

    # PastParties
    def get_price_with_refunds(self):
        return self.get_price() - self.purchase_refund()

    def purchase_refund(self):
        return sum([r.get_price() for r in self.refunds])

    def purchase_promoter_cut(self):
        return self.get_price_with_refunds() * self.promoter_commission / 100

    def purchase_club_owner_cut(self):
        return self.get_price_with_refunds() * self.club_owner_commission / 100

    def purchase_date(self):
        return self.purchase_datetime.strftime("%d-%m-%Y %H:%M")

    def refund_json(self):
        return {
            "purchase_id": self.purchase_id,
            "name": self.name,
            "email": self.email,
            "purchase_date": self.purchase_date(),
            "entrance_code": self.entrance_code(),
            "party_id": self.party.party_id,
            "party_title": self.party.title,
            "party_date": self.party.party_date(),
            "price": self.get_price(),
            "number_of_tickers": len(self.tickets),
            "refunds": [r.refund_json() for r in self.refunds],
            "status": self.status
        }


class Refund(db.Model, TrackModifications):
    __tablename__ = REFUND
    refund_id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer, nullable=False, default=0)
    refund_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    purchase_id = db.Column(db.Integer, db.ForeignKey(f"{PURCHASE}.purchase_id"))
    purchase = db.relationship('Purchase', back_populates='refunds', single_parent=True)
    mollie_refund_id = db.Column(db.String(128), nullable=False, default="")

    def set_price(self, price_float):
        self.price = int(price_float * 100)

    def get_price(self):
        return float(self.price)/100

    def refund_json(self):
        return {
            "refund_id": self.refund_id,
            "price": self.get_price(),
            "mollie_refund_id": self.mollie_refund_id,
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

    def promoter(self):
        if self.user is None:
            return "-"
        return self.user

    def deactivate(self):
        self.active = False
        self.user = None

    def qr_code(self):
        url = pyqrcode.create(url_for("main.index", code=self.code, _external=True))
        return url.png_as_base64_str(scale=10)


class File(db.Model, TrackModifications):
    __tablename__ = FILE
    file_id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(256), nullable=False)
    type = db.Column(db.String(128), nullable=False)
    party_id = db.Column(db.Integer, db.ForeignKey(f"{PARTY}.party_id"))
    # party = db.relationship('Party', back_populates='files')
    parties = db.relationship("Party", secondary=party_file_table)

    def url(self):
        return"{static}{file}"\
            .format(static=current_app.static_url_path, file=self.path.split("static")[1].replace('\\', '/'))
