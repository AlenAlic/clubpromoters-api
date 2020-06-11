from flask import request
from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, StringField
from wtforms.validators import DataRequired, NumberRange
from constants import GET
from models.configuration import config


class InvoiceSettingsForm(FlaskForm):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if request.method == GET:
            conf = config()
            self.invoice_legal_name.data = conf.invoice_legal_name
            self.invoice_street.data = conf.invoice_street
            self.invoice_street_number.data = conf.invoice_street_number
            self.invoice_street_number_addition.data = conf.invoice_street_number_addition
            self.invoice_postal_code.data = conf.invoice_postal_code
            self.invoice_postal_code_letters.data = conf.invoice_postal_code_letters
            self.invoice_city.data = conf.invoice_city
            self.invoice_kvk_number.data = conf.invoice_kvk_number
            self.invoice_vat_number.data = conf.invoice_vat_number
            self.invoice_vat.data = conf.invoice_vat
            self.invoice_email_address.data = conf.invoice_email_address
            self.invoice_iban.data = conf.invoice_iban

    invoice_legal_name = StringField("Legal name", validators=[DataRequired()])
    invoice_street = StringField("Street", validators=[DataRequired()])
    invoice_street_number = IntegerField("Number", validators=[DataRequired(), NumberRange(0)])
    invoice_street_number_addition = StringField("Addition")
    invoice_postal_code = IntegerField("Postal code", validators=[DataRequired(), NumberRange(1000, 9999)])
    invoice_postal_code_letters = StringField("Postal code letters", validators=[DataRequired()])
    invoice_city = StringField("City", validators=[DataRequired()])
    invoice_kvk_number = StringField("KVK number", validators=[DataRequired()])
    invoice_vat_number = StringField("VAT number", validators=[DataRequired()])
    invoice_vat = IntegerField("VAT for invoices", validators=[DataRequired(), NumberRange(0, 99)])
    invoice_iban = StringField("IBAN", validators=[DataRequired()])
    invoice_email_address = StringField("Invoice e-mail", validators=[DataRequired()])
    save_changes = SubmitField("Save changes")

    def save(self):
        conf = config()
        conf.invoice_legal_name = self.invoice_legal_name.data
        conf.invoice_street = self.invoice_street.data
        conf.invoice_street_number = self.invoice_street_number.data
        conf.invoice_street_number_addition = self.invoice_street_number_addition.data
        conf.invoice_postal_code = self.invoice_postal_code.data
        conf.invoice_postal_code_letters = self.invoice_postal_code_letters.data
        conf.invoice_city = self.invoice_city.data
        conf.invoice_kvk_number = self.invoice_kvk_number.data
        conf.invoice_vat_number = self.invoice_vat_number.data
        conf.invoice_vat = self.invoice_vat.data
        conf.invoice_iban = self.invoice_iban.data
        conf.invoice_email_address = self.invoice_email_address.data
