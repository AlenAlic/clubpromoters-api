from flask import Blueprint

bp = Blueprint('club_owner', __name__)

from backend.club_owner import routes
