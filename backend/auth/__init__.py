from flask import Blueprint

bp = Blueprint('auth', __name__)

from backend.auth import routes
