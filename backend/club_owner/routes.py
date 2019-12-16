from flask import json, request, jsonify
from backend import db
from flask_login import login_required, current_user
from backend.club_owner import bp
from backend.values import *
from backend.models import requires_access_level, User, Party
from backend.util import auth_token
from backend.auth.email import send_activation_email
from datetime import datetime
from backend.util import last_month_datetime
from sqlalchemy import func


@bp.route('/create_new_hostess', methods=[POST])
@login_required
@requires_access_level([AL_CLUB_OWNER])
def create_new_hostess():
    form = json.loads(request.data)
    account = User()
    account.email = form["email"]
    account.first_name = form["first_name"]
    account.last_name = form["last_name"]
    account.activation_code = auth_token()
    account.access = AL_HOSTESS
    account.working = True
    account.club_owner = current_user
    send_activation_email(account)
    db.session.add(account)
    db.session.commit()
    send_activation_email(account)
    return OK


@bp.route('/hostesses', methods=[GET])
@login_required
@requires_access_level([AL_CLUB_OWNER])
def users():
    u = User.query.filter(User.access == AL_HOSTESS, User.club_owner_id == current_user.user_id).all()
    return jsonify([user.json() for user in u])


@bp.route('/activate_hostess/<int:hostess_id>', methods=[PATCH])
@login_required
@requires_access_level([AL_CLUB_OWNER])
def activate_hostess(hostess_id):
    form = json.loads(request.data)
    hostess = User.query.filter(User.user_id == hostess_id).first()
    hostess.working = form["working"]
    db.session.commit()
    return OK


@bp.route('/inactive_parties', methods=[GET])
@requires_access_level([AL_CLUB_OWNER])
def inactive_parties():
    parties = Party.query.filter(Party.is_active.is_(False), Party.party_end_datetime > datetime.utcnow(),
                                 Party.club_owner == current_user).order_by(Party.party_start_datetime).all()
    return jsonify([p.json() for p in parties])


@bp.route('/active_parties', methods=[GET])
@requires_access_level([AL_CLUB_OWNER])
def active_parties():
    parties = Party.query.filter(Party.is_active.is_(True), Party.party_end_datetime > datetime.utcnow(),
                                 Party.club_owner == current_user).order_by(Party.party_start_datetime).all()
    return jsonify([p.json() for p in parties])


@bp.route('/past_parties', methods=[GET])
@login_required
@requires_access_level([AL_CLUB_OWNER])
def past_parties():
    parties = Party.query.filter(Party.is_active.is_(True), Party.party_end_datetime < datetime.utcnow(),
                                 Party.club_owner == current_user).order_by(Party.party_start_datetime).all()
    return jsonify([p.json() for p in parties])


def parties_list(year, month):
    last_month = last_month_datetime(year, month)
    party = Party.query.filter(Party.is_active.is_(True), Party.party_end_datetime < datetime.now(),
                               Party.club_owner == current_user,
                               func.month(Party.party_end_datetime) == func.month(last_month),
                               func.year(Party.party_end_datetime) == func.year(last_month)).all()
    return [p.json() for p in party]


@bp.route('/party_income/<int:year>/<int:month>', methods=[GET])
@login_required
@requires_access_level([AL_CLUB_OWNER])
def party_income(year, month):
    return jsonify(parties_list(year, month))
