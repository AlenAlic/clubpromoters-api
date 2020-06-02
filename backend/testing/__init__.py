from flask import Blueprint

bp = Blueprint('testing', __name__)

from backend.testing import routes
