from flask import g, current_app
from flask_login import current_user
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


def upload_file(file, user):
    if file.filename != "" and (allowed_file(file.filename) or file.mimetype == "application/pdf"):
        filename = secure_filename(file.filename)
        directory = os.path.join(current_app.static_folder, UPLOAD_FOLDER, f"{user.user_id}")
        path = os.path.join(directory, f"{time()}.{file_extension(filename)}")
        if File.query.filter(File.path == path).first() is not None:
            return None
        if not os.path.exists(directory):
            os.makedirs(directory)
        file.save(path)
        db_file = File()
        db_file.user = user
        db_file.name = filename
        db_file.path = path
        db.session.add(db_file)
        db.session.commit()
        return db_file
    return None


def upload_image(file, user, logo=False):
    db_file = upload_file(file, user)
    if db_file is not None:
        db_file.logo = logo
        db.session.commit()
    return db_file


def last_month_datetime(year, month):
    last_month = datetime(year, month, 1)
    previous_month = last_month.month - 1 or 12
    if previous_month == 1:
        last_month.replace(year=last_month.year - 1)
    return last_month
