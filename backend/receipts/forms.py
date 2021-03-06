from flask import request
from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, StringField, FloatField, TextAreaField
from wtforms.validators import DataRequired, NumberRange
from constants import GET
from models.configuration import config
from utilities import euro_to_cents, cents_to_euro


class ReceiptSettingsForm(FlaskForm):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if request.method == GET:
            conf = config()
            self.administration_costs.data = cents_to_euro(conf.administration_costs)
            self.vat.data = conf.vat
            self.receipt_title.data = conf.receipt_title
            self.receipt_address.data = conf.receipt_address
            self.receipt_city.data = conf.receipt_city
            self.receipt_country.data = conf.receipt_country
            self.receipt_phone.data = conf.receipt_phone
            self.receipt_email.data = conf.receipt_email

    administration_costs = FloatField("Administration costs €", validators=[DataRequired(), NumberRange(0)])
    vat = IntegerField("VAT percentage", validators=[DataRequired()])
    receipt_title = StringField("Company name (or website)", validators=[DataRequired()])
    receipt_address = StringField("Address", validators=[DataRequired()])
    receipt_city = StringField("City", validators=[DataRequired()])
    receipt_country = StringField("Country", validators=[DataRequired()])
    receipt_phone = StringField("Phone number")
    receipt_email = StringField("E-mail", validators=[DataRequired()])
    save_changes = SubmitField("Save changes")

    def save(self):
        conf = config()
        conf.administration_costs = euro_to_cents(self.administration_costs.data)
        conf.vat = self.vat.data
        conf.receipt_title = self.receipt_title.data
        conf.receipt_address = self.receipt_address.data
        conf.receipt_city = self.receipt_city.data
        conf.receipt_country = self.receipt_country.data
        conf.receipt_phone = self.receipt_phone.data
        conf.receipt_email = self.receipt_email.data


class TicketSettingsForm(FlaskForm):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if request.method == GET:
            conf = config()
            self.ticket_footer_text.data = conf.ticket_footer_text

    ticket_footer_text = TextAreaField("Ticket footer", render_kw={"rows": 4})
    save_changes = SubmitField("Save changes")

    def save(self):
        conf = config()
        conf.ticket_footer_text = self.ticket_footer_text.data
