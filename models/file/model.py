from ext import db
from models.tables import TABLE_FILE, TABLE_USERS
from models import TrackModifications
from flask import current_app, request
import urllib.parse


class File(db.Model, TrackModifications):
    __tablename__ = TABLE_FILE
    file_id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(256), nullable=False)
    logo = db.Column(db.Boolean, nullable=False, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey(f"{TABLE_USERS}.user_id"))
    user = db.relationship('User', back_populates='files')

    def __repr__(self):
        return f"{self.file_id}: {self.name}"

    @property
    def directory(self):
        return self.path.replace('\\', '/').rsplit("\\", 1)[0]

    @property
    def filename(self):
        return self.path.replace('\\', '/').rsplit("\\", 1)[1]

    def url(self):
        relative_url = "{static}{file}"\
            .format(static=current_app.static_url_path, file=self.path.split("static")[1].replace('\\', '/'))
        url = f"{request.scheme}://{request.host}{relative_url}"
        return urllib.parse.quote(url, safe="/:")

    def json(self):
        data = {
            "id": self.file_id,
            "url": self.url(),
            "name": self.name,
            "logo": self.logo,
            "user_id": self.user_id,
        }
        return data
