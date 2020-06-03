from flask import Blueprint

bp = Blueprint("settings", __name__)

from backend.settings import routes
