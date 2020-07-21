from flask import Blueprint

bp = Blueprint('demo', __name__)

from backend.demo import routes
