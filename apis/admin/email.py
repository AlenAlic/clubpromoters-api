from flask import render_template, current_app
from flask_login import current_user
from mailing import send_email


def send_activation_email(user):
    send_email(
        f"Activate account at {current_app.config['PRETTY_URL']}",
        recipients=[user.email],
        text_body=render_template("email/auth/activate_account.txt", user=user),
        html_body=render_template("email/auth/activate_account.html", user=user)
    )


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email(
        f"Password reset at {current_app.config['PRETTY_URL']}.",
        recipients=[user.email],
        text_body=render_template("email/auth/reset_password.txt", user=user, token=token),
        html_body=render_template("email/auth/reset_password.html", user=user, token=token)
    )


def send_password_changed_email():
    send_email(
        f"Password changed at {current_app.config['PRETTY_URL']}.",
        recipients=[current_user.email],
        text_body=render_template("email/auth/password_changed.txt"),
        html_body=render_template("email/auth/password_changed.html")
    )
