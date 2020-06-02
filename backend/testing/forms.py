from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class CreateTestAccountsForm(FlaskForm):
    password = StringField("Password", validators=[DataRequired()])
    number = IntegerField("Number of accounts", validators=[DataRequired(), NumberRange(1, 10)])
    club_owners = BooleanField("Club Owners")
    promoters = BooleanField("Promoters")
    submit = SubmitField("Create accounts")
