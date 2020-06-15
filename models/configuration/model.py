from ext import db
from models.tables import TABLE_CONFIGURATION, TABLE_FILE
from models import TrackModifications
from utilities import cents_to_euro


class Configuration(db.Model, TrackModifications):
    __tablename__ = TABLE_CONFIGURATION
    lock_id = db.Column(db.Integer, primary_key=True)
    mollie_api_key = db.Column(db.String(128))
    allowed_image_types = db.Column(db.String(256), nullable=False,
                                    default="jpg,jpeg,png", server_default="jpg,jpeg,png")
    default_club_owner_commission = db.Column(db.Integer, nullable=False, default=10)
    default_promoter_commission = db.Column(db.Integer, nullable=False, default=15)
    site_available = db.Column(db.Boolean, nullable=False, default=False)
    test_email = db.Column(db.String(128))
    terms_id = db.Column(db.Integer, db.ForeignKey(f"{TABLE_FILE}.file_id"))
    terms = db.relationship("File")
    minimum_promoter_commission = db.Column(db.Integer, nullable=False, default=100)
    administration_costs = db.Column(db.Integer, nullable=False, default=0)
    vat = db.Column(db.Integer(), nullable=False, default=9)
    receipt_title = db.Column(db.String(128))
    receipt_address = db.Column(db.String(128))
    receipt_country = db.Column(db.String(128))
    receipt_phone = db.Column(db.String(128))
    invoice_legal_name = db.Column(db.String(128), nullable=False)
    invoice_street = db.Column(db.String(256), nullable=False)
    invoice_street_number = db.Column(db.String(12), nullable=False)
    invoice_street_number_addition = db.Column(db.String(12), default="")
    invoice_postal_code = db.Column(db.Integer(), nullable=False)
    invoice_postal_code_letters = db.Column(db.String(2), nullable=False)
    invoice_city = db.Column(db.String(256), nullable=False)
    invoice_email_address = db.Column(db.String(128), nullable=False)
    invoice_kvk_number = db.Column(db.String(128), nullable=False)
    invoice_vat_number = db.Column(db.String(128), nullable=False)
    invoice_iban = db.Column(db.String(30), nullable=False)
    invoice_vat = db.Column(db.Integer(), nullable=False, default=21)
    bookkeeping_program_email = db.Column(db.String(256), nullable=False)

    def allowed_file_types(self):
        return self.allowed_image_types.split(",")

    @property
    def invoice_street_line(self):
        return f"{self.invoice_street} {self.invoice_street_number}{self.invoice_street_number_addition}"

    @property
    def invoice_postal_code_line(self):
        return f"{self.invoice_postal_code} {self.invoice_postal_code_letters}, {self.invoice_city}"

    def json(self):
        return {
            "default_club_owner_commission": self.default_club_owner_commission,
            "default_promoter_commission": self.default_promoter_commission,
            "mollie_api_key": self.mollie_api_key,
            "test_email": self.test_email,
            "terms": self.terms.url if self.terms else None,
            "minimum_promoter_commission": cents_to_euro(self.minimum_promoter_commission),
            "administration_costs": cents_to_euro(self.administration_costs),
        }
