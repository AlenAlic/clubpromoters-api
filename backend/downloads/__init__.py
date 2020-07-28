from flask import Blueprint

bp = Blueprint("downloads", __name__)

from backend.downloads import routes
