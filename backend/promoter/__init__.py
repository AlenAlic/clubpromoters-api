from flask import Blueprint

bp = Blueprint('promoter', __name__)

from backend.promoter import routes
