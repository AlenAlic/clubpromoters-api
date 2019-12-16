from flask import Blueprint

bp = Blueprint('self_admin', __name__)

from backend.admin import routes
