from flask import render_template, current_app
from mailing import send_email
from mailing.util import filtered_form
from datetime import datetime


def send_error_email(code, error, trace):
    form = filtered_form()
    send_email(
        f"Error: {code}; {current_app.config['PRETTY_URL']} {datetime.utcnow().strftime('%d-%m-%Y, @%H:%M:%S')}",
        recipients=[current_app.config["ERROR_EMAIL"]],
        text_body=render_template("email/error/trace.txt", status_code=code, error=error, trace=trace, form=form),
        html_body=render_template("email/error/trace.html", status_code=code, error=error, trace=trace, form=form)
    )
