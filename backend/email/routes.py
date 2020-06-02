from flask import render_template, redirect, url_for, flash
from backend.email import bp
from constants import GET
from mailing.util import filtered_form
from models import User
from utilities import activation_code


GROUP_ERROR = "error"
NAME_TRACE = "trace"
GROUP_AUTH = "auth"
NAME_ACTIVATE_ACCOUNT = "activate_account"
NAME_RESET_PASSWORD = "reset_password"
NAME_PASSWORD_CHANGED = "password_changed"


@bp.route("/", methods=[GET])
def index():
    email_list = [
        {
            "group": GROUP_ERROR,
            "emails": {
                NAME_TRACE: "Server error"
            }
        },
        {
            "group": GROUP_AUTH,
            "emails": {
                NAME_ACTIVATE_ACCOUNT: "Account activation",
                NAME_RESET_PASSWORD: "New password requested",
                NAME_PASSWORD_CHANGED: "Password has been changed",
            }
        }
    ]
    return render_template("email/index.html", email_list=email_list)


@bp.route("/preview/<string:group>/<string:name>", methods=[GET])
def preview(group, name):
    return render_template("email/preview.html", group=group, name=name)


@bp.route("/template/<string:group>/<string:name>", methods=[GET])
def template(group, name):
    path = f"email/{group}/{name}.html"
    if group == GROUP_ERROR:
        if name == NAME_TRACE:
            trace = [
                'Traceback (most recent call last):',
                '  File "C:\\Users\\Alen\\PycharmProjects\\flask-api-boilerplate\\.venv\\lib\\site-'
                'packages\\flask\\app.py", line 1928, in full_dispatch_request',
                '    rv = self.dispatch_request()',
                '  File "C:\\Users\\Alen\\PycharmProjects\\flask-api-boilerplate\\.venv\\lib\\site-'
                'packages\\flask\\app.py", line 1914, in dispatch_request',
                '    return self.view_functions[rule.endpoint](**req.view_args)'
                '  File "C:\\Users\\Alen\\PycharmProjects\\flask-api-boilerplate\\backend\\email\\routes.py", line 32, '
                'in template',
                '    "trace": render_template(path, status_code=500, error=error, trace=trace, form=filtered_form())',
                "NameError: name 'error' is not defined"
            ]
            error = 'name \'error\' is not defined'
            return render_template(path, status_code=500, error=error, trace=trace, form=filtered_form())
    if group == GROUP_AUTH:
        if name == NAME_ACTIVATE_ACCOUNT:
            usr = User("alice@test.com")
            usr.first_name = "Alice"
            usr.auth_code = activation_code()
            return render_template(path, user=usr)
        if name == NAME_RESET_PASSWORD:
            usr = User("bob@test.com", "test")
            usr.first_name = "Bob"
            usr.is_active = True
            return render_template(path, user=usr, token=usr.get_reset_password_token())
        if name == NAME_PASSWORD_CHANGED:
            return render_template(path)
    flash("Dit not find e-mail template.")
    return redirect(url_for("email.index"))
