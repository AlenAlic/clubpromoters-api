from models import User, Invoice
from sqlalchemy import func
from datetime import datetime


def generate_serial_number(user):
    invoices = Invoice.query.filter(Invoice.user == user, func.year(Invoice.date) == func.year(datetime.utcnow())).all()
    return len(invoices) + 1
