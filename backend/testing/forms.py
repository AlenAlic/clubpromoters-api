from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Email
from wtforms.fields.html5 import EmailField
from models.configuration import config
from constants import GET


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
