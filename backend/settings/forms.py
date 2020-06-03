from flask import request
from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, StringField, FloatField, FileField
from wtforms.validators import DataRequired, NumberRange
from constants import GET
from models.configuration import config


class SettingsForm(FlaskForm):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if request.method == GET:
            conf = config()
            self.default_club_owner_commission.data = conf.default_club_owner_commission
            self.default_promoter_commission.data = conf.default_promoter_commission
            self.minimum_promoter_commission.data = conf.get_minimum_promoter_commission()
            self.mollie_api_key.data = conf.mollie_api_key

    default_club_owner_commission = IntegerField("Default Club Owner commission %",
                                                 validators=[DataRequired(), NumberRange(0, 50)])
    default_promoter_commission = IntegerField("Default Promoter commission %",
                                               validators=[DataRequired(), NumberRange(0, 50)])
    minimum_promoter_commission = FloatField("Minimum promoter commission €",
                                             validators=[DataRequired(), NumberRange(0)])
    mollie_api_key = StringField("Mollie API key", validators=[DataRequired()])
    save_settings = SubmitField("Save changes")

    def save(self):
        conf = config()
        conf.default_club_owner_commission = self.default_club_owner_commission.data
        conf.default_promoter_commission = self.default_promoter_commission.data
        conf.set_minimum_promoter_commission(self.minimum_promoter_commission.data)
        conf.mollie_api_key = self.mollie_api_key


class TermsForm(FlaskForm):

    terms = FileField("Terms and conditions", validators=[DataRequired()])
    upload_terms = SubmitField("Upload terms")


class RemoveTermsForm(FlaskForm):

    remove_terms = SubmitField("Remove terms")
