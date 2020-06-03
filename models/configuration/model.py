from ext import db
from models.tables import TABLE_CONFIGURATION, TABLE_FILE
from models import TrackModifications


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
    vat = db.Column(db.Integer(), nullable=False, default=21)
    invoice_title = db.Column(db.String(128))
    invoice_address = db.Column(db.String(128))
    invoice_country = db.Column(db.String(128))
    invoice_phone = db.Column(db.String(128))

    def allowed_file_types(self):
        return self.allowed_image_types.split(",")

    def get_minimum_promoter_commission(self):
        return float(self.minimum_promoter_commission)/100

    def set_minimum_promoter_commission(self, price_float):
        self.minimum_promoter_commission = int(float(price_float) * 100)

    def get_administration_costs(self):
        return float(self.administration_costs)/100

    def set_administration_costs(self, price_float):
        self.administration_costs = int(float(price_float) * 100)

    def json(self):
        return {
            "default_club_owner_commission": self.default_club_owner_commission,
            "default_promoter_commission": self.default_promoter_commission,
            "mollie_api_key": self.mollie_api_key,
            "test_email": self.test_email,
            "terms": self.terms.url() if self.terms else None,
            "minimum_promoter_commission": self.get_minimum_promoter_commission(),
            "administration_costs": self.get_administration_costs(),
        }