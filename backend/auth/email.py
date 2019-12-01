from flask import render_template
from backend.email import send_email


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('Password reset', recipients=[user.email],
               text_body=render_template('email/reset_password.txt', user=user, token=token),
               html_body=render_template('email/reset_password.html', user=user, token=token))


def send_activation_email(user):
    send_email('Activate account', recipients=[user.email],
               text_body=render_template('email/activate_account.txt', user=user),
               html_body=render_template('email/activate_account.html', user=user))
