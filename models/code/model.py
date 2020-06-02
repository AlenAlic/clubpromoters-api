from ext import db
from models.tables import TABLE_CODE, TABLE_USERS
from models import TrackModifications
from flask import current_app
from flask_login import current_user
import pyqrcode


class Code(db.Model, TrackModifications):
    __tablename__ = TABLE_CODE
    code_id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey(f"{TABLE_USERS}.user_id"))
    user = db.relationship('User', back_populates='code', single_parent=True)
    purchases = db.relationship('Purchase', back_populates='code')

    def __repr__(self):
        return self.code

    def deactivate(self):
        self.active = False
        self.user_id = None

    def qr_code(self):
        url = pyqrcode.create(f"{current_app.config.get('BASE_URL')}?code={self.code}")
        return url.png_as_base64_str(scale=10)

    def json(self):
        data = {
            "id": self.code_id,
            "code": self.code,
            "active": self.active,
        }
        if current_user.is_promoter:
            data.update({
                "qr_code": self.qr_code(),
            })
        if self.user_id is not None:
            data["promoter"] = {
                "id": self.user.user_id,
                "name": self.user.full_name
            }
        return data
