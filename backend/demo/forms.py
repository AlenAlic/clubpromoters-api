from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from constants import LOCAL_TIMEZONE
from models import Party
from datetime import datetime, timedelta
import pytz
from random import choice
from .data import CURRENT_PARTY_DAYS, PAST_PARTY_DAYS
from .functions import create_party, preset_start_datetime
from sqlalchemy import func


class CreateDemoClubsForm(FlaskForm):
    password = StringField("Password", validators=[DataRequired()])
    create_clubs = SubmitField("Create demo clubs, codes, and promoters")


class CreateCurrentPartiesForm(FlaskForm):

    create_current_parties = SubmitField("Create new parties starting tonight")

    @staticmethod
    def save(clubs):
        start_date = preset_start_datetime()
        for club in clubs:
            for day in CURRENT_PARTY_DAYS:
                if day == 0 or choice([True, True, False]):
                    create_party(club, start_date + timedelta(days=day))


class CreatePastPartiesForm(FlaskForm):

    create_past_parties = SubmitField("Create past parties")

    @staticmethod
    def save(clubs):
        now = datetime.utcnow()
        start_date = preset_start_datetime()
        start_date = start_date.replace(month=1, day=1)
        for month in range(1, now.month + 1):
            parties = Party.query.filter(Party.is_active.is_(True),
                                         func.month(Party.party_start_datetime) == func.month(start_date),
                                         func.year(Party.party_start_datetime) == func.year(start_date)).all()
            if len(parties) == 0:
                for club in clubs:
                    for day in PAST_PARTY_DAYS:
                        if choice([True, True, False]) and (month < now.month or day < now.day):
                            create_party(club, start_date + timedelta(days=day))
            if start_date.month < now.month:
                start_date = start_date.replace(month=start_date.month + 1)


