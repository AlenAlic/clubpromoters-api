from flask import Blueprint

bp = Blueprint('hostess', __name__)

from backend.hostess import routes
