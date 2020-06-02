from flask import jsonify, json, request, redirect, url_for, flash, current_app, g
from flask_login import login_user, logout_user, login_required, current_user
from backend.admin import bp
from backend.models import requires_access_level, User, Code, Party, Purchase, Ticket, File, Refund
from backend.values import *
from backend import db
from backend.auth.email import send_activation_email
from backend.util import auth_token
import random
import string
from datetime import datetime, timezone, timedelta
import shutil
import os


@bp.route('/switch', methods=[GET], defaults={"user_id": None})
@bp.route('/switch/<int:user_id>', methods=[POST])
@login_required
@requires_access_level([ACCESS_ADMIN])
def switch(user_id):
    if request.method == GET:
        users = User.query.filter(User.access != ACCESS_ADMIN, User.is_active.is_(True)).all()
        return jsonify([{"text": u.email, "value": u.user_id} for u in users])
    if request.method == POST:
        u = User.query.filter(User.access != ACCESS_ADMIN, User.is_active.is_(True), User.user_id == user_id).first()
        if u is not None:
            return jsonify(u.get_auth_token())
        else:
            return BAD_REQUEST


@bp.route('/has_organizer', methods=[GET])
@login_required
@requires_access_level([ACCESS_ADMIN])
def has_organizer():
    if request.method == GET:
        users = User.query.filter(User.access == ACCESS_ORGANIZER).count()
        return jsonify(users > 0)


@bp.route('/create_organizer_account', methods=[POST])
@login_required
def setup():
    form = json.loads(request.data)
    organizer = User()
    organizer.email = form["email"]
    organizer.access = ACCESS_ORGANIZER
    organizer.auth_code = auth_token()
    db.session.add(organizer)
    db.session.commit()
    send_activation_email(organizer)
    return OK
