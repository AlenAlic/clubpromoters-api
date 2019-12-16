from flask import jsonify
from flask_login import login_required, current_user
from backend.promoter import bp
from backend.values import *
from backend.models import requires_access_level


@bp.route('/code', methods=[GET])
@login_required
@requires_access_level([AL_PROMOTER])
def code():
    return jsonify(current_user.code.json() if current_user.code else None)
