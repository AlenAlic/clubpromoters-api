from flask_login import current_user
from models import Party
from datetime import datetime
from sqlalchemy import func


def parties_list(year, month):
    dt = datetime(year, month, 1)
    party = Party.query.filter(Party.is_active.is_(True), Party.party_end_datetime < datetime.utcnow(),
                               Party.club_owner == current_user,
                               func.month(Party.party_end_datetime) == func.month(dt),
                               func.year(Party.party_end_datetime) == func.year(dt)).all()
    return [p.json() for p in party]
