from flask import jsonify, json, request
from backend.main import bp
from backend.values import *
from backend.models import Party, Code
from datetime import datetime


@bp.route('/ping', methods=[GET])
def ping():
    return OK


@bp.route('/party/<int:party_id>', methods=[GET])
def party(party_id):
    p = Party.query.filter(Party.is_active.is_(True), Party.party_end_datetime > datetime.utcnow(),
                           Party.party_id == party_id).first()
    return jsonify(p.json())


@bp.route('/active_parties', methods=[GET])
def active_parties():
    parties = Party.query.filter(Party.is_active.is_(True), Party.party_end_datetime > datetime.utcnow())\
        .order_by(Party.party_start_datetime).all()
    return jsonify([p.json() for p in parties])


@bp.route('/homepage_parties', methods=[GET])
def homepage_parties():
    parties = Party.query.filter(Party.is_active.is_(True), Party.party_end_datetime > datetime.utcnow())\
        .order_by(Party.party_start_datetime, Party.party_id).all()
    if len(parties) == 0:
        return jsonify([])
    min_date = min([p.party_start_datetime for p in parties])
    parties = [p for p in parties if p.party_start_datetime == min_date]
    return jsonify([p.json() for p in parties])


@bp.route('/check_code', methods=[POST])
def check_code():
    form = json.loads(request.data)
    code = Code.query.filter(Code.active.is_(True), Code.code == form["code"]).first()
    if code is not None:
        return OK
    return BAD_REQUEST
