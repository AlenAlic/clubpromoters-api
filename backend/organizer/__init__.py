from flask import Blueprint

bp = Blueprint('organizer', __name__)

from backend.organizer import routes
