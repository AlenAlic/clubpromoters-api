from threading import Thread
from flask import current_app
from flask_mail import Message
from ext import mail
from models.configuration import config


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, recipients, text_body, html_body, cc=None, bcc=None, attachments=None):
    if current_app.config["DEBUG"] and config().test_email:
        recipients = [config().test_email]
        cc = cc if cc else [config().test_email]
        bcc = bcc if bcc else [config().test_email]
    msg = Message(subject, recipients=recipients, cc=cc, bcc=bcc)
    msg.body = text_body
    msg.html = html_body
    if attachments:
        for name, attachment in attachments.items():
            with current_app.open_resource(attachment) as file:
                msg.attach(filename=name, content_type="text/plain", data=file.read())
    # noinspection PyProtectedMember
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
