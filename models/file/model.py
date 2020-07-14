from ext import db
from models.tables import TABLE_FILE, TABLE_USERS, TABLE_PARTY_FILES
from models import TrackModifications
from flask import current_app, request
import urllib.parse
from sqlalchemy.ext.associationproxy import association_proxy
import os
import contextlib


class File(db.Model, TrackModifications):
    __tablename__ = TABLE_FILE
    file_id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(256), nullable=False)
    logo = db.Column(db.Boolean, nullable=False, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey(f"{TABLE_USERS}.user_id"))
    user = db.relationship("User", back_populates="files")
    parties = association_proxy(TABLE_PARTY_FILES, "party")

    def __repr__(self):
        return f"{self.file_id}: {self.name}"

    @property
    def directory(self):
        return self.path.replace("\\", "/").rsplit("/", 1)[0]

    @property
    def filename(self):
        return self.path.replace("\\", "/").rsplit("/", 1)[1]

    @property
    def url(self):
        scheme = "http" if "127.0.0.1" in request.host or "localhost" in request.host else "https"
        relative_url = "{static}{file}"\
            .format(static=current_app.static_url_path, file=self.path.split("static")[1].replace("\\", "/"))
        url = f"{scheme}://{request.host}{relative_url}"
        return urllib.parse.quote(url, safe="/:")

    @property
    def deletable(self):
        if not self.logo:
            return len(self.parties) == 0
        else:
            from models.party import Party
            return len(Party.query.filter(Party.logo == self).all()) == 0

    def remove_from_disk(self):
        with contextlib.suppress(FileNotFoundError):
            os.remove(self.path)

    def json(self):
        data = {
            "id": self.file_id,
            "url": self.url,
            "name": self.name,
            "logo": self.logo,
            "user_id": self.user_id,
            "deletable": self.deletable,
        }
        return data
