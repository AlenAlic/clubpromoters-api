from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, IntegerField, SubmitField, DateField
from wtforms.validators import DataRequired, NumberRange
from wtforms.fields.html5 import EmailField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from models.configuration import config
from constants import GET, LOCAL_TIMEZONE
from models import User, File, Party, PartyFile
from models.user.constants import ACCESS_CLUB_OWNER
from datetime import datetime, timedelta
from ext import db
import pytz
from random import choice, shuffle


class CreateTestAccountsForm(FlaskForm):
    password = StringField("Password", validators=[DataRequired()])
    number = IntegerField("Number of accounts", validators=[DataRequired(), NumberRange(1, 10)])
    club_owners = BooleanField("Club Owners")
    promoters = BooleanField("Promoters")
    create_accounts = SubmitField("Create accounts")


class TestEmailForm(FlaskForm):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if request.method == GET:
            conf = config()
            self.test_email.data = conf.test_email

    test_email = EmailField("Testing e-mail")
    save_email = SubmitField("Save e-mail")

    def save(self):
        conf = config()
        conf.test_email = self.test_email.data


SYNONYMS = ["Awesome", "Astonishing", "Amazing", "Imposing", "Impressive", "Grand", "Mind-blowing", "Striking"]


class TestPartyForm(FlaskForm):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.club_owner.query = User.query.filter(User.access == ACCESS_CLUB_OWNER, User.locations.any(),
                                                  User.files.any(File.logo.is_(True)),
                                                  User.files.any(File.logo.is_(False)))

    club_owner = QuerySelectField("Club Owner", validators=[DataRequired()])
    number = IntegerField("Number of parties (every additional party will be one day later than the previous)",
                          validators=[DataRequired(), NumberRange(1, 10)])
    date = DateField("Start date", validators=[DataRequired()])
    create_parties = SubmitField("Create parties")

    def save(self):
        date = self.date.data
        start_date = datetime(date.year, date.month, date.day, 22, 30)
        amsterdam_start_date = LOCAL_TIMEZONE.localize(start_date)
        for i in range(self.number.data):
            start_date = amsterdam_start_date.astimezone(pytz.utc) + timedelta(days=i)
            party = Party()
            party.club_owner = self.club_owner.data
            party.name = f"{choice(SYNONYMS)} party"
            party.location = self.club_owner.data.locations[0]
            party.party_start_datetime = start_date + timedelta(hours=choice([-1, 0, 1]))
            party.party_end_datetime = party.party_start_datetime + timedelta(hours=choice([5, 6, 7]))
            party.description = "Description here"
            party.num_available_tickets = choice([80, 100, 120, 140, 150])
            party.ticket_price = choice([1500, 2000, 2500, 3000, 4000, 5000])
            party.club_owner_commission = 20
            party.promoter_commission = 15
            logos = [f for f in party.club_owner.files if f.logo]
            shuffle(logos)
            party.logo = logos[0]
            images = [f for f in party.club_owner.files if not f.logo]
            shuffle(images)
            for idx, file in enumerate(images):
                party_file = PartyFile()
                party_file.order = idx
                party_file.file = file
                party_file.party = party
            db.session.add(party)
