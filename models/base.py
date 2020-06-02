from flask import current_app
from datetime import datetime
from jwt import decode, ExpiredSignatureError
from contextlib import suppress
from random import choice
from string import ascii_letters
from ext import db


class TrackModifications(object):
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def get_token_from_request(req):
    token = req.headers.get("Authorization")
    if token is not None:
        return decode_token(token.replace("Bearer ", ""))
    return None


def decode_token(token):
    with suppress(ExpiredSignatureError):
        return decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    return None


def auth_token():
    allowed_chars = ascii_letters + "0123456789"
    return "".join([choice(allowed_chars) for _ in range(128)])


def table_exists(model):
    return db.engine.dialect.has_table(db.engine, model.__tablename__)


def get_code_from_request(req):
    from models import Code
    code = req.headers.get("Code")
    return Code.query.filter(Code.active.is_(True), Code.code == code).first()
