from models import Party, Purchase, User, Invoice
from sqlalchemy import func, or_
from models.user.constants import ACCESS_CLUB_OWNER, ACCESS_PROMOTER
from datetime import datetime
import re


def parties_list(year, month):
    dt = datetime(year, month, 1)
    party = Party.query.filter(Party.is_active.is_(True),
                               func.month(Party.party_start_datetime) == func.month(dt),
                               func.year(Party.party_start_datetime) == func.year(dt)).all()
    return [p.json() for p in party]


def purchases_list(year, month):
    dt = datetime(year, month, 1)
    purchase = Purchase.query.filter(func.month(Purchase.purchase_datetime) == func.month(dt),
                                     func.year(Purchase.purchase_datetime) == func.year(dt)).all()
    return [p.json() for p in purchase]


def commissions(last_month, filter_users=True):
    parties = Party.query.filter(func.month(Party.party_start_datetime) == func.month(last_month),
                                 func.year(Party.party_start_datetime) == func.year(last_month))\
        .order_by(Party.party_start_datetime).all()
    purchases = [purchase for party in parties for purchase in party.purchases]
    users = User.query.filter(or_(User.access == ACCESS_CLUB_OWNER, User.access == ACCESS_PROMOTER),
                              User.is_active.is_(True)).all()
    if filter_users:
        promoters = list(set([purchase.promoter_id for purchase in purchases]))
        club_owners = list(set([p.club_owner_id for p in parties]))
        users = User.query.filter(User.user_id.in_(club_owners + promoters), User.is_active.is_(True)).all()
        users = [user for user in users if len(user.invoice_parties(last_month)) > 0]
    return [user.commissions_json(user.invoice_parties(last_month)) for user in users]


def this_months_invoices(date):
    invoices = Invoice.query.join(User).filter(func.year(Invoice.date) == func.year(date),
                                               func.month(Invoice.date) == func.month(date))\
        .order_by(User.access, User.club, User.first_name).all()
    return invoices


def get_location_string(maps_url):
    if maps_url.startswith("http"):
        return maps_url
    else:
        match = re.search("(?<=src=\")(.*?)(?=\")", maps_url)
        if match:
            span = match.span()
            return maps_url[span[0]:span[1]]
    return ""
