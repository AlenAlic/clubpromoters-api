from flask import Blueprint

bp = Blueprint("receipts", __name__)

from backend.receipts import routes
