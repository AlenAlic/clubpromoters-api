from ext import db, login
from models.tables import TABLE_USERS
from models import TrackModifications
from models.base import get_token_from_request
from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from .constants import ACCESS_ADMIN, ACCESS_ORGANIZER, ACCESS_CLUB_OWNER, ACCESS_HOSTESS, ACCESS_PROMOTER
from werkzeug.security import generate_password_hash, check_password_hash
from constants import SECONDS_DAY, SECONDS_QUARTER
from jwt import encode, decode
from jwt.exceptions import InvalidTokenError
from time import time
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func
from constants.mollie import STATUS_PAID
from models.party import Party
from models.purchase import Purchase
from utilities import datetime_browser, cents_to_euro


class Anonymous(AnonymousUserMixin):

    @hybrid_property
    def is_admin(self):
        return False

    @property
    def profile(self):
        return {}

    @staticmethod
    def is_organizer():
        return False

    @staticmethod
    def is_club_owner():
        return False

    @staticmethod
    def is_promoter():
        return False

    @staticmethod
    def is_hostess():
        return False

    @staticmethod
    def allowed():
        return False

    @staticmethod
    def last_seen():
        return None


@login.request_loader
def load_user(req):
    data = get_token_from_request(req)
    if data is not None:
        try:
            user_id = data["id"]
            reset_index = data["reset_index"]
            return User.query.filter(User.user_id == user_id, User.reset_index == reset_index).first()
        except (InvalidTokenError, AttributeError, KeyError):
            return None
    return None


@login.user_loader
def load_user(user_id):
    try:
        user_id, reset_index = user_id.split("-")
        return User.query.filter(User.user_id == user_id, User.reset_index == reset_index).first()
    except (AttributeError, ValueError):
        return None


class User(UserMixin, Anonymous, db.Model, TrackModifications):
    __tablename__ = TABLE_USERS
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

    def __init__(self, email=None, password=None):
        self.email = email
        if password:
            self.set_password(password)

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @hybrid_property
    def is_admin(self):
        return self.access == ACCESS_ADMIN

    @hybrid_property
    def is_organizer(self):
        return self.access == ACCESS_ORGANIZER

    @hybrid_property
    def is_club_owner(self):
        return self.access == ACCESS_CLUB_OWNER

    @hybrid_property
    def is_promoter(self):
        return self.access == ACCESS_PROMOTER

    @hybrid_property
    def is_hostess(self):
        return self.access == ACCESS_HOSTESS

    def set_password(self, password, increment=True):
        self.password_hash = generate_password_hash(password)
        if self.reset_index is not None and increment:
            self.reset_index += 1

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=SECONDS_QUARTER):
        return encode({
            "reset_password": self.user_id,
            "exp": time() + expires_in
        }, current_app.config["SECRET_KEY"], algorithm="HS256").decode("utf-8")

    @staticmethod
    def verify_reset_password_token(token):
        try:
            user_id = decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])["reset_password"]
        except InvalidTokenError:
            return None
        return User.query.get(user_id)

    def get_auth_token(self, expires_in=SECONDS_DAY):
        return encode({
            "id": self.user_id,
            "reset_index": self.reset_index,
            "email": self.email,
            "access": self.access,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "iat": time(),
            "exp": time() + expires_in,
        }, current_app.config["SECRET_KEY"], algorithm="HS256").decode("utf-8")

    @property
    def profile(self):
        data = {
            "id": self.user_id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
        }
        if self.is_club_owner:
            data.update({
                "club": self.club,
                "commission": self.commission,
                "iban": self.iban,
            })
        if self.is_promoter:
            data.update({
                "code": self.code.json() if self.code else None,
                "commission": self.commission,
                "iban": self.iban,
            })
        return data

    def assets(self):
        return {
            "images": [file.json() for file in self.files if not file.logo],
            "logos": [file.json() for file in self.files if file.logo],
        }

    def json(self):
        data = {
            "id": self.user_id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "name": self.full_name,
            "access": self.access,
            "is_active": self.is_active,
            "last_seen": datetime_browser(self.last_seen),
        }
        if self.is_club_owner:
            data.update({
                "locations": [loc.json() for loc in self.locations],
                "hostesses": [{
                    "id": h.user_id,
                    "email": h.email,
                    "name": h.full_name,
                    "last_seen": datetime_browser(h.last_seen),
                    "is_active": h.is_active,
                } for h in self.hostesses],
                "commission": self.commission,
                "club": self.club,
            })
        if self.is_promoter:
            data.update({
                "commission": self.commission,
            })
            if self.code is not None:
                data.update({
                    "code": self.code.json(),
                })
        if self.is_hostess:
            data.update({
                "working": self.working,
            })
        return data

    def commissions_json(self, purchases):
        data = {
            'id': self.user_id,
            "full_name": self.full_name,
            "access": self.access,
        }
        total = 0
        if self.is_promoter:
            purchases = [p for p in purchases if p.promoter == self and p.status == STATUS_PAID]
            total = sum([p.income_promoter_commissions for p in purchases])
            parties = Party.query.filter(Party.party_id.in_([p.party_id for p in purchases if p.promoter == self])) \
                .order_by(Party.party_start_datetime).all()
            data.update({
                "parties": [p.promoter_commissions(self) for p in parties]
            })
        if self.is_club_owner:
            purchases = [p for p in purchases if p.party.club_owner == self and p.status == STATUS_PAID]
            total = sum([p.income_club_owner_commissions for p in purchases])
            parties = Party.query.filter(Party.party_id.in_([p.party_id for p in purchases])) \
                .order_by(Party.party_start_datetime).all()
            data.update({
                "club": self.club,
                "parties": [p.json() for p in parties],
            })
        data.update({
            "total": cents_to_euro(total),
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
            "parties": [p.promoter_commissions(self) for p in parties],
            "total": total,
        }
        return data
