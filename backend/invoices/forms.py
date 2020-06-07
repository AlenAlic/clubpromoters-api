from flask import request
from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, StringField, FloatField
from wtforms.validators import DataRequired, NumberRange
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from models import Purchase
from constants import GET
from models.configuration import config
from utilities import euro_to_cents, cents_to_euro


class TestInvoiceForm(FlaskForm):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.purchase.query = Purchase.query

    purchase = QuerySelectField("Purchase", validators=[DataRequired()])
    view_invoice = SubmitField("View invoice")


class InvoiceSettingsForm(FlaskForm):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if request.method == GET:
            conf = config()
            self.administration_costs.data = cents_to_euro(conf.administration_costs)
            self.vat.data = conf.vat
            self.invoice_title.data = conf.invoice_title
            self.invoice_address.data = conf.invoice_address
            self.invoice_country.data = conf.invoice_country
            self.invoice_phone.data = conf.invoice_phone

    administration_costs = FloatField("Administration costs €", validators=[DataRequired(), NumberRange(0)])
    vat = IntegerField("VAT percentage", validators=[DataRequired()])
    invoice_title = StringField("Company name (or website)", validators=[DataRequired()])
    invoice_address = StringField("Address", validators=[DataRequired()])
    invoice_country = StringField("Country", validators=[DataRequired()])
    invoice_phone = StringField("Phone number", validators=[DataRequired()])
    save_changes = SubmitField("Save changes")

    def save(self):
        conf = config()
        conf.administration_costs = euro_to_cents(self.administration_costs.data)
        conf.vat = self.vat.data
        conf.invoice_title = self.invoice_title.data
        conf.invoice_address = self.invoice_address.data
        conf.invoice_country = self.invoice_country.data
        conf.invoice_phone = self.invoice_phone.data
