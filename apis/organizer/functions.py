from utilities import last_month_datetime
from models import Party, Purchase
from sqlalchemy import func


def parties_list(year, month):
    last_month = last_month_datetime(year, month)
    party = Party.query.filter(Party.is_active.is_(True),
                               func.month(Party.party_start_datetime) == func.month(last_month),
                               func.year(Party.party_start_datetime) == func.year(last_month)).all()
    return [p.json() for p in party]


def purchases_list(year, month):
    last_month = last_month_datetime(year, month)
    purchase = Purchase.query.filter(func.month(Purchase.purchase_datetime) == func.month(last_month),
                                     func.year(Purchase.purchase_datetime) == func.year(last_month)).all()
    return [p.json() for p in purchase]
