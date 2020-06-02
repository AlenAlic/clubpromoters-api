from flask import Blueprint

bp = Blueprint("email", __name__)

#from backend.email import routes

# TEMP
from threading import Thread
from flask import current_app, g
from flask_mail import Message
from backend import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, recipients, text_body, html_body, cc=None, bcc=None):
    if current_app.config['DEBUG'] and g.config.test_email is not None and g.config.test_email != "":
        recipients = [g.config.test_email]
    msg = Message(subject, recipients=recipients, cc=cc, bcc=bcc)
    msg.body = text_body
    msg.html = html_body
    # noinspection PyProtectedMember
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
