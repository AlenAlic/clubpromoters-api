from flask import g, send_from_directory
from backend.documents import bp
from backend.values import *


@bp.route('/terms', methods=[GET])
def terms():
    file = g.config.terms
    if file is not None:
        return send_from_directory(file.directory, filename=file.filename)
    return ""
