from flask import jsonify, request, json, render_template, current_app
from flask_login import login_required, current_user
from backend.auth import bp
from backend.models import User, get_token_from_request
from backend.values import *
from backend import db
from backend.util import auth_token
from backend.email import send_email
import re


def send_account_activation_email(u):
    send_email(f"Account activation {current_app.config['PRETTY_URL']}.",
               recipients=[u.email],
               text_body=render_template('email/activate_account.txt', user=u),
               html_body=render_template('email/activate_account.html', user=u))


@bp.route('/create', methods=[POST])
@login_required
def create():
    form = json.loads(request.data)
    u = User.query.filter(User.email.ilike(form["email"])).first()
    if u is None:
        u = User()
        u.first_name = form["first_name"]
        u.last_name = form["last_name"]
        u.email = form["email"]
        u.access = form["account"]
        u.auth_code = auth_token()
        db.session.add(u)
        db.session.commit()
        send_account_activation_email(u)
        return OK
    return BAD_REQUEST


def check_password_requirements(new_password, repeat_password):
    equal = new_password == repeat_password
    length = len(new_password) >= MINIMAL_PASSWORD_LENGTH
    lowercase = re.search("[a-z]", new_password)
    uppercase = re.search("[A-Z]", new_password)
    number = re.search("[0-9]", new_password)
    return all([equal, length, lowercase, uppercase, number])


@bp.route('/activate/<string:token>', methods=[GET, POST])
def activate(token):
    u = User.query.filter(User.auth_code == token).first()
    if u is not None:
        if request.method == GET:
            return OK
        if request.method == POST:
            form = json.loads(request.data)
            if check_password_requirements(form["password"], form["repeat_password"]):
                u.set_password(form["password"])
                u.auth_code = None
                u.is_active = True
                db.session.commit()
                return OK
            return BAD_REQUEST
    else:
        return NOT_FOUND


@bp.route('/login', methods=[POST])
def login():
    form = json.loads(request.data)
    u = User.query.filter(User.email.ilike(form["email"])).first()
    if u is None or not u.check_password(form["password"]):
        return UNAUTHORIZED
    elif u.is_active:
        return jsonify(u.get_auth_token(expires_in=SECONDS_MONTH if form["remember_me"] else SECONDS_DAY))
    return UNAUTHORIZED


@bp.route('/renew', methods=[GET])
@login_required
def renew():
    data = get_token_from_request(request)
    return jsonify(current_user.get_auth_token(expires_in=int(data["exp"]-data["iat"])))


@bp.route('/logout', methods=[DELETE])
@login_required
def logout():
    return OK


@bp.route('/user/<int:user_id>', methods=[GET])
@login_required
def user(user_id):
    u = User.query.filter(User.user_id == user_id).first()
    if u is not None:
        return u.profile()
    else:
        return BAD_REQUEST


@bp.route('/password/change/<int:user_id>', methods=[PATCH])
@login_required
def password(user_id):
    u = User.query.filter(User.user_id == user_id).first()
    form = json.loads(request.data)
    if u.check_password(form["current_password"]):
        if check_password_requirements(form["new_password"], form["repeat_password"]) \
                and form["new_password"] != form["current_password"]:
            u.set_password(form["new_password"], increment=False)
            db.session.commit()
            return OK
        else:
            return BAD_REQUEST
    return UNAUTHORIZED


def send_password_reset_email(u):
    token = u.get_reset_password_token(expires_in=SECONDS_QUARTER)
    send_email(f"Password reset {current_app.config['PRETTY_URL']}.",
               recipients=[u.email],
               text_body=render_template('email/reset_password.txt', user=u, token=token),
               html_body=render_template('email/reset_password.html', user=u, token=token))


@bp.route('/password/reset', methods=[POST], defaults={"token": None})
@bp.route('/password/reset/<string:token>', methods=[PATCH])
def reset_password(token):
    if request.method == POST:
        data = json.loads(request.data)
        u = User.query.filter(User.email.ilike(data["email"])).first()
        if u is not None:
            send_password_reset_email(u)
        return OK
    if request.method == PATCH:
        u = User.verify_reset_password_token(token)
        if u:
            if not u.is_active:
                return BAD_REQUEST
            form = json.loads(request.data)
            if form["password"] == form["repeat_password"]:
                u.set_password(form["password"])
                u.auth_code = None
                u.is_active = True
                db.session.commit()
                return OK
            return UNAUTHORIZED
        return BAD_REQUEST
