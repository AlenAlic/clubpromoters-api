from flask import Blueprint

bp = Blueprint('purchase', __name__)

from backend.purchase import routes
