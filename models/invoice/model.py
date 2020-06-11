from ext import db
from models.tables import TABLE_INVOICE, TABLE_USERS
from models import TrackModifications
from .constants import DUTCH
from datetime import datetime, timedelta
import locale


class Invoice(db.Model, TrackModifications):
    __tablename__ = TABLE_INVOICE
    invoice_id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(256), nullable=False)
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
    invoice_country = db.Column(db.String(256), nullable=False)
    invoice_kvk_number = db.Column(db.String(128), nullable=False)
    invoice_vat_number = db.Column(db.String(128), nullable=False)
    invoice_phone_number = db.Column(db.String(128), nullable=False)
    invoice_iban = db.Column(db.String(128), nullable=False)
    invoice_vat = db.Column(db.Integer(), nullable=False, default=21)
    user_id = db.Column(db.Integer, db.ForeignKey(f"{TABLE_USERS}.user_id"))
    user = db.relationship("User", back_populates="invoices")
    parties = db.relationship("Party", back_populates="invoice")

    def __repr__(self):
        return f"{self.invoice_id}: {self.filename}"

    @property
    def directory(self):
        return self.path.replace("\\", "/").rsplit("/", 1)[0]

    @property
    def filename(self):
        return self.path.replace("\\", "/").rsplit("/", 1)[1]

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
        return int(self.total * 100 / (100 + self.invoice_vat))

    @property
    def vat_total(self):
        return self.total - self.total_no_vat

    @property
    def total(self):
        return sum([party.income_club_owner_commission for party in self.parties])

    @property
    def delivery_date(self):
        locale.setlocale(locale.LC_ALL, self.language)
        delivery_date = self.date.replace(month=self.date.month - 1 or 12)
        delivery_date = delivery_date.strftime("%B %Y")
        locale.setlocale(locale.LC_ALL, 'C')
        return delivery_date

    @property
    def due_date(self):
        locale.setlocale(locale.LC_ALL, self.language)
        due_date = self.expiration_date.strftime("%d %B %Y")
        locale.setlocale(locale.LC_ALL, 'C')
        return due_date

    def json(self):
        return {
            "id": self.invoice_id,
        }
