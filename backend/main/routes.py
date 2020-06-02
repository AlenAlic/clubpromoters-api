from flask import jsonify, json, request, g
from flask_login import login_required
from backend.main import bp
from backend.models import requires_access_level
from backend import db
from backend.values import *
from backend.models import Party, Code, User
from datetime import datetime
from backend.util import upload_image


@bp.route('/ping', methods=[GET])
def ping():
    return OK



@bp.route('/public/party/<int:party_id>', methods=[GET])
def party(party_id):
    p = Party.query.filter(Party.is_active.is_(True), Party.party_end_datetime > datetime.utcnow(),
                           Party.party_id == party_id).first()
    return jsonify({
        "party": p.json(),
        "settings": g.config.json(),
    })


@bp.route('/public/active_parties', methods=[GET])
def active_parties():
    parties = Party.query.filter(Party.is_active.is_(True), Party.party_end_datetime > datetime.utcnow())\
        .order_by(Party.party_start_datetime).all()
    return jsonify([p.json() for p in parties])


@bp.route('/public/homepage_parties', methods=[GET])
def homepage_parties():
    parties = Party.query.filter(Party.is_active.is_(True), Party.party_end_datetime > datetime.utcnow())\
        .order_by(Party.party_start_datetime, Party.party_id).all()
    if len(parties) == 0:
        return jsonify([])
    min_date = min([p.party_start_datetime for p in parties])
    parties = [p for p in parties if p.party_start_datetime == min_date]
    return jsonify([p.json() for p in parties])


@bp.route('/public/check_code', methods=[POST])
def check_code():
    form = json.loads(request.data)
    code = Code.query.filter(Code.active.is_(True), Code.code == form["code"]).first()
    if code is not None:
        return OK
    return BAD_REQUEST


@bp.route('/user/upload/images/<int:user_id>', methods=[POST])
@login_required
@requires_access_level([AL_ORGANIZER, AL_CLUB_OWNER])
def upload_images(user_id):
    user = User.query.filter(User.user_id == user_id).first()
    form = request.form
    files = request.files
    for image in files:
        upload_image(files[image], user, logo=form["logo"] == "true")
    db.session.commit()
    return OK


@bp.route('/user/assets/<int:user_id>', methods=[GET])
@login_required
@requires_access_level([AL_ORGANIZER, AL_CLUB_OWNER])
def assets(user_id):
    user = User.query.filter(User.user_id == user_id).first()
    return user.assets()
