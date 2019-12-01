from threading import Thread
from flask import current_app
from flask_mail import Message
from backend import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, recipients, text_body, html_body, cc=None, bcc=None):
    msg = Message(subject, recipients=recipients, cc=cc, bcc=bcc)
    msg.body = text_body
    msg.html = html_body
    # noinspection PyProtectedMember
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
