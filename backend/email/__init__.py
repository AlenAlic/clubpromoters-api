from flask import Blueprint

bp = Blueprint("email", __name__)

from backend.email import routes
