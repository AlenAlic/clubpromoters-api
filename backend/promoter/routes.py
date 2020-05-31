from flask import jsonify
from flask_login import login_required, current_user
from backend.promoter import bp
from backend.values import *
from backend.models import requires_access_level
from backend.util import last_month_datetime


@bp.route('/code', methods=[GET])
@login_required
@requires_access_level([AL_PROMOTER])
def code():
    return jsonify(current_user.code.json() if current_user.code else None)


@bp.route('/income/<int:year>/<int:month>', methods=[GET])
@login_required
@requires_access_level([AL_PROMOTER])
def income(year, month):
    return jsonify(current_user.promoter_income(last_month_datetime(year, month)))
