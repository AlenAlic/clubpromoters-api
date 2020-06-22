from flask import current_app, render_template, request
from ext import db
from models.tables import TABLE_INVOICE, TABLE_USERS, TABLE_PARTY_INVOICE
from models import TrackModifications
from .constants import DUTCH
from datetime import datetime, timedelta
import locale
from weasyprint import HTML
import os
from models.configuration import config
from models.user.constants import ACCESS_CLUB_OWNER, ACCESS_PROMOTER
from utilities import datetime_browser


class Invoice(db.Model, TrackModifications):
    __tablename__ = TABLE_INVOICE
    invoice_id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(256))
    year = db.Column(db.Integer(), nullable=False)
    serial_number = db.Column(db.Integer(), nullable=False)
    business_invoice = db.Column(db.Boolean, nullable=False, default=False)
    language = db.Column(db.String(128), nullable=False, default=DUTCH)
    sent = db.Column(db.Boolean, nullable=False, default=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    cp_legal_name = db.Column(db.String(128), nullable=False)
    cp_street = db.Column(db.String(256), nullable=False)
    cp_street_number = db.Column(db.String(12), nullable=False)
    cp_street_number_addition = db.Column(db.String(12), default="")
    cp_postal_code = db.Column(db.Integer(), nullable=False)
    cp_postal_code_letters = db.Column(db.String(2), nullable=False)
    cp_city = db.Column(db.String(256), nullable=False)
    cp_kvk_number = db.Column(db.String(128), nullable=False)
    cp_vat_number = db.Column(db.String(128), nullable=False)
    cp_iban = db.Column(db.String(128), nullable=False)
    cp_email_address = db.Column(db.String(128), nullable=False)
    invoice_legal_name = db.Column(db.String(128), nullable=False)
    invoice_street = db.Column(db.String(256), nullable=False)
    invoice_street_number = db.Column(db.String(12), nullable=False)
    invoice_street_number_addition = db.Column(db.String(12), default="")
    invoice_postal_code = db.Column(db.Integer(), nullable=False)
    invoice_postal_code_letters = db.Column(db.String(2), nullable=False)
    invoice_city = db.Column(db.String(256), nullable=False)
    invoice_country = db.Column(db.String(256))
    invoice_kvk_number = db.Column(db.String(128))
    invoice_vat_number = db.Column(db.String(128))
    invoice_phone_number = db.Column(db.String(128), nullable=False)
    invoice_iban = db.Column(db.String(128), nullable=False)
    invoice_vat = db.Column(db.Integer(), nullable=False, default=21)
    user_id = db.Column(db.Integer, db.ForeignKey(f"{TABLE_USERS}.user_id"))
    user = db.relationship("User", back_populates="invoices")
    parties = db.relationship("Party", secondary=TABLE_PARTY_INVOICE)

    def __repr__(self):
        return f"{self.invoice_id}: {self.filename}"

    def __init__(self, user, parties, serial_number):
        conf = config()
        self.user = user
        self.business_invoice = user.business_entity or user.access == ACCESS_CLUB_OWNER
        self.parties.extend(parties)
        self.serial_number = serial_number
        self.year = datetime.utcnow().year

        self.invoice_vat = conf.invoice_vat

        self.cp_legal_name = conf.invoice_legal_name
        self.cp_street = conf.invoice_street
        self.cp_street_number = conf.invoice_street_number
        self.cp_street_number_addition = conf.invoice_street_number_addition
        self.cp_postal_code = conf.invoice_postal_code
        self.cp_postal_code_letters = conf.invoice_postal_code_letters
        self.cp_city = conf.invoice_city
        self.cp_kvk_number = conf.invoice_kvk_number
        self.cp_vat_number = conf.invoice_vat_number
        self.cp_iban = conf.invoice_iban
        self.cp_email_address = conf.invoice_email_address

        self.invoice_legal_name = user.invoice_legal_name
        self.invoice_street = user.street
        self.invoice_street_number = user.street_number
        self.invoice_street_number_addition = user.street_number_addition
        self.invoice_postal_code = user.postal_code
        self.invoice_postal_code_letters = user.postal_code_letters
        self.invoice_city = user.city
        self.invoice_phone_number = user.phone_number
        self.invoice_iban = user.iban
        self.invoice_country = user.country
        if self.business_invoice:
            self.invoice_kvk_number = user.invoice_kvk_number
            self.invoice_vat_number = user.invoice_vat_number

    def generate_invoice(self):
        path = os.path.join(current_app.invoices_folder, f"{self.invoice_number}.pdf")
        HTML(string=render_template("invoices/invoice_template.html", invoice=self),
             base_url=request.base_url).write_pdf(path)
        self.path = path

    @property
    def directory(self):
        return self.path.replace("\\", "/").rsplit("/", 1)[0]

    @property
    def filename(self):
        return self.path.replace("\\", "/").rsplit("/", 1)[1]

    @property
    def promoter_invoice(self):
        return self.user.access == ACCESS_PROMOTER

    @property
    def cp_street_line(self):
        return f"{self.cp_street} {self.cp_street_number}{self.cp_street_number_addition}"

    @property
    def cp_postal_code_line(self):
        return f"{self.cp_postal_code} {self.cp_postal_code_letters}, {self.cp_city}"

    @property
    def invoice_number(self):
        customer_number = f"{self.user_id}".zfill(6)
        serial_number = f"{self.serial_number}".zfill(4)
        return f"CP{customer_number}{self.year}{serial_number}"

    @property
    def invoice_street_line(self):
        return f"{self.invoice_street} {self.invoice_street_number}{self.invoice_street_number_addition}"

    @property
    def invoice_postal_code_line(self):
        return f"{self.invoice_postal_code} {self.invoice_postal_code_letters}, {self.invoice_city}"

    @property
    def expiration_date(self):
        return self.date + timedelta(days=30)

    @property
    def total_no_vat(self):
        if self.business_invoice:
            return int(self.total * 100 / (100 + self.invoice_vat))
        return self.total

    @property
    def vat_total(self):
        return self.total - self.total_no_vat

    @property
    def total(self):
        if self.promoter_invoice:
            return sum([party.income_promoter_commission(self.user) for party in self.parties])
        else:
            return sum([party.income_club_owner_commission for party in self.parties])

    @property
    def delivery_datetime(self):
        return self.date.replace(month=self.date.month - 1 or 12)

    @property
    def delivery_date(self):
        locale.setlocale(locale.LC_ALL, self.language)
        delivery_date = self.delivery_datetime.strftime("%B %Y")
        locale.setlocale(locale.LC_ALL, 'C')
        return delivery_date

    @property
    def due_date(self):
        locale.setlocale(locale.LC_ALL, self.language)
        due_date = self.expiration_date.strftime("%d %B %Y")
        locale.setlocale(locale.LC_ALL, 'C')
        return due_date

    @property
    def dutch(self):
        return self.language == DUTCH

    def send(self):
        from apis.organizer.email import send_invoice
        send_invoice(self)
        self.sent = True

    def json(self):
        data = {
            "id": self.invoice_id,
            "name": self.user.full_name if self.promoter_invoice else self.user.club,
            "filename": self.filename,
            "promoter_invoice": self.promoter_invoice,
            "sent": self.sent,
            "delivery_datetime": datetime_browser(self.delivery_datetime),
            "invoice_number": self.invoice_number,
            "user": {
                "id": self.user.user_id,
                "full_name": self.user.full_name,
                "club": self.user.club,
                "email": self.user.email,
            }
        }
        return data
