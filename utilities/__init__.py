from flask import current_app
from datetime import datetime
from constants import DATETIME_FORMAT
from random import choice
from string import ascii_letters
import os
from werkzeug.utils import secure_filename
from models.file import File
from ext import db
from time import time
from constants import UPLOAD_FOLDER


def datetime_python(s):
    return datetime.strptime(s, DATETIME_FORMAT)


def datetime_browser(dt):
    return dt.strftime(DATETIME_FORMAT)


def cents_to_euro(cents):
    return float(cents)/100


def euro_to_cents(euro):
    return int(euro * 100)


def activation_code():
    allowed_chars = ascii_letters + '0123456789'
    token = ''.join([choice(allowed_chars) for _ in range(128)])
    token += str(int(datetime.utcnow().timestamp() * 10**6))
    return token[-128:]


def format_euro(price):
    if price > 0:
        p = '€{:,.2f}'.format(price)
        p = p.replace(".00", "")
        return p
    else:
        return '€0'


def last_month_datetime(year, month):
    last_month = datetime(year, month, 1)
    previous_month = last_month.month - 1 or 12
    if previous_month == 1:
        last_month.replace(year=last_month.year - 1)
    return last_month


def file_extension(filename):
    return filename.rsplit('.', 1)[1].lower()


def allowed_file(filename):
    from models.configuration import config
    return '.' in filename and file_extension(filename) in config().allowed_file_types()


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
