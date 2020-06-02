from flask import Blueprint

bp = Blueprint('purchase_bp', __name__)

from backend.purchase import routes
