from flask_login import current_user
from models import Party
from datetime import datetime
from utilities import last_month_datetime
from sqlalchemy import func


def parties_list(year, month):
    last_month = last_month_datetime(year, month)
    party = Party.query.filter(Party.is_active.is_(True), Party.party_end_datetime < datetime.now(),
                               Party.club_owner == current_user,
                               func.month(Party.party_end_datetime) == func.month(last_month),
                               func.year(Party.party_end_datetime) == func.year(last_month)).all()
    return [p.json() for p in party]
