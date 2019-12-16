from flask import Blueprint

bp = Blueprint('mollie_webhook', __name__)

from backend.mollie_webhook import routes


@bp.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    return response
