from flask import g, current_app
from backend import db
import os
from werkzeug.utils import secure_filename
from datetime import timezone, datetime
from time import time
from backend.values import DATETIME_FORMAT, UPLOAD_FOLDER
from random import choice
import string
from backend.models import File


def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)


def datetime_python(s):
    return datetime.strptime(s, DATETIME_FORMAT)


def auth_token():
    allowed_chars = string.ascii_letters + '0123456789'
    return ''.join([choice(allowed_chars) for _ in range(128)])


def file_extension(filename):
    return filename.rsplit('.', 1)[1].lower()


def allowed_file(filename):
    return '.' in filename and file_extension(filename) in g.config.allowed_file_types()


def upload_file(file, club_owner, file_type):
    if file.filename != "" and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        directory = os.path.join(current_app.static_folder, UPLOAD_FOLDER, club_owner.club)
        path = os.path.join(directory, f"{time()}.{file_extension(filename)}")
        if File.query.filter(File.path == path).first() is not None:
            # flash(f"Could not upload file {filename} ({file_type}). Please try again")
            return None
        if not os.path.exists(directory):
            os.makedirs(directory)
        file.save(path)
        db_file = File()
        db_file.user = club_owner
        db_file.type = file_type
        db_file.name = filename
        db_file.path = path
        db.session.add(db_file)
        db.session.commit()
        # flash(f"File uploaded {filename} ({file_type}).")
        return db_file
    return None


def last_month_datetime(year, month):
    last_month = datetime(year, month, 1)
    previous_month = last_month.month - 1 or 12
    if previous_month == 1:
        last_month.replace(year=last_month.year - 1)
    return last_month
