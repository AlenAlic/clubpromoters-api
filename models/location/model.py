from ext import db
from models.tables import TABLE_LOCATION, TABLE_USERS
from models import TrackModifications


class Location(db.Model, TrackModifications):
    __tablename__ = TABLE_LOCATION
    location_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    street = db.Column(db.String(256), nullable=False)
    street_number = db.Column(db.String(12), nullable=False)
    street_number_addition = db.Column(db.String(12))
    postal_code = db.Column(db.Integer(), nullable=False)
    postal_code_letters = db.Column(db.String(2), nullable=False)
    city = db.Column(db.String(256), nullable=False)
    maps_url = db.Column(db.String(512))
    user_id = db.Column(db.Integer, db.ForeignKey(f"{TABLE_USERS}.user_id"))
    user = db.relationship('User', back_populates='locations')
    parties = db.relationship('Party', back_populates='location')

    def __repr__(self):
        return f"{self.location_id}: {self.name}"

    def json(self):
        data = {
            "id": self.location_id,
            "name": self.name,
            "street": self.street,
            "street_number": self.street_number,
            "street_number_addition": self.street_number_addition,
            "postal_code": self.postal_code,
            "postal_code_letters": self.postal_code_letters,
            "city": self.city,
            "maps_url": self.maps_url,
            "user_id": self.user_id,
        }
        return data
