from flask import json, request, jsonify
from backend import db
from flask_login import login_required, current_user
from backend.hostess import bp
from backend.values import *
from backend.models import requires_access_level, User, Party, Purchase
from datetime import datetime


@bp.route('/parties', methods=[GET])
@login_required
@requires_access_level([AL_HOSTESS])
def hostess_parties():
    parties = Party.query.filter(Party.is_active.is_(True), Party.party_end_datetime > datetime.utcnow(),
                                 Party.club_owner_id == current_user.club_owner_id)\
        .order_by(Party.party_start_datetime).all()
    parties = [p for p in parties if p.party_start_datetime.date() == datetime.utcnow().date()]
    return jsonify([p.json() for p in parties])


@bp.route('/party/<int:party_id>', methods=[GET])
@login_required
@requires_access_level([AL_HOSTESS])
def party(party_id):
    purchases = Purchase.query.filter(Purchase.party_id == party_id).all()
    p = Party.query.filter(Party.party_id == party_id).first()
    return jsonify({"party": p.json(), "purchases": [p.json() for p in purchases]})


@bp.route('/entrance_code', methods=[POST])
@login_required
@requires_access_level([AL_HOSTESS])
def entrance_code():
    form = json.loads(request.data)
    purchase = Purchase.query.filter(Purchase.hash == form["entrance_code"]).first()
    if purchase is None:
        return NOT_FOUND
    available_tickets = [t for t in purchase.tickets if t.available()]
    if len(available_tickets) > 0:
        return jsonify(purchase.json())
    return BAD_REQUEST


@bp.route('/accept', methods=[POST])
@login_required
@requires_access_level([AL_HOSTESS])
def accept():
    form = json.loads(request.data)
    purchase = Purchase.query.filter(Purchase.purchase_id == form["purchase_id"]).first()
    tickets = form["tickets"]
    available_tickets = [t for t in purchase.tickets if t.available()]
    if len(available_tickets) >= tickets:
        for i in range(tickets):
            available_tickets[i].used = True
        db.session.commit()
        return OK
    return BAD_REQUEST


@bp.route('/deny', methods=[POST])
@login_required
@requires_access_level([AL_HOSTESS])
def deny():
    form = json.loads(request.data)
    purchase = Purchase.query.filter(Purchase.purchase_id == form["purchase_id"]).first()
    tickets = form["tickets"]
    available_tickets = [t for t in purchase.tickets if t.available()]
    if len(available_tickets) >= tickets:
        for i in range(tickets):
            available_tickets[i].denied_entry = True
        db.session.commit()
        return OK
    return BAD_REQUEST
