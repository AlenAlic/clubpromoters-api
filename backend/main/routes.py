from backend.main import bp
from backend.values import *


@bp.route('/ping', methods=[GET])
def ping():
    return OK
