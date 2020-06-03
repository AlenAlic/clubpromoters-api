from flask import Blueprint

bp = Blueprint("invoices", __name__)

from backend.invoices import routes
