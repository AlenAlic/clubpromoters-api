from flask import Blueprint

bp = Blueprint("preview", __name__)

from backend.preview import routes
