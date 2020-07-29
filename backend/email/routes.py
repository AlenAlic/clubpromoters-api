from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user
from backend.email import bp
from constants import GET, POST
from mailing.util import filtered_form
from models import User, Purchase, Party, Invoice
from utilities import activation_code
from .functions import generate_dummy_purchase, send_test_email


GROUP_ERROR = "error"
NAME_TRACE = "trace"
GROUP_AUTH = "auth"
NAME_ACTIVATE_ACCOUNT = "activate_account"
NAME_RESET_PASSWORD = "reset_password"
NAME_PASSWORD_CHANGED = "password_changed"
GROUP_PURCHASE = "purchase"
NAME_PURCHASE = "purchased_tickets"
NAME_RECEIPT = "receipt"
NAME_REFUND = "refund_receipt"
GROUP_INVOICES = "invoices"
NAME_SEND_INVOICE = "send_invoice"


@bp.route("/", methods=[GET, POST])
def index():
    email_list = [
        {
            "group": GROUP_AUTH,
            "emails": {
                NAME_ACTIVATE_ACCOUNT: "Account activation",
                NAME_RESET_PASSWORD: "New password requested",
                NAME_PASSWORD_CHANGED: "Password has been changed",
            }
        },
        {
            "group": GROUP_PURCHASE,
            "emails": {
                NAME_PURCHASE: "Tickets",
                NAME_RECEIPT: "Receipt",
                NAME_REFUND: "Refund receipt",
            }
        },
        {
            "group": GROUP_INVOICES,
            "emails": {
                NAME_SEND_INVOICE: "Invoice sent",
            }
        }
    ]
    if current_user.is_admin:
        email_list.insert(0, {
            "group": GROUP_ERROR,
            "emails": {
                NAME_TRACE: "Server error"
            }
        })
    if request.method == POST and current_user.is_admin:
        if "send_test_email" in request.form and (current_app.config["DEBUG"] or current_app.config["DEMO"]):
            send_test_email()
            flash("Test e-mail sent.")
        else:
            flash("Could not send test e-mail.", "warning")
        return redirect(url_for("email.index"))
    return render_template("email/index.html", email_list=email_list)


@bp.route("/preview/<string:group>/<string:name>", methods=[GET])
def preview(group, name):
    groups = [GROUP_ERROR, GROUP_AUTH, GROUP_PURCHASE, GROUP_INVOICES]
    names = [NAME_TRACE, NAME_ACTIVATE_ACCOUNT, NAME_RESET_PASSWORD, NAME_PASSWORD_CHANGED, NAME_PURCHASE,
             NAME_RECEIPT, NAME_REFUND, NAME_SEND_INVOICE]
    if group not in groups or name not in names:
        flash("Dit not find e-mail template.")
        return redirect(url_for("email.index"))
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
    if group == GROUP_PURCHASE:
        if name == NAME_PURCHASE or name == NAME_RECEIPT:
            purchase = Purchase.query.first()
            if not purchase:
                purchase = generate_dummy_purchase()
            return render_template(path, purchase=purchase)
        if name == NAME_REFUND:
            purchase = generate_dummy_purchase()
            return render_template(path, refund=purchase.refunds[0])
    if group == GROUP_INVOICES:
        if name == NAME_SEND_INVOICE:
            invoice = Invoice.query.first()
            if not invoice:
                usr = User("charlie@test.com", "test")
                usr.first_name = "Charlie"
                usr.is_active = True
                invoice = Invoice(usr, [Party(), Party()], 42)
            return render_template(path, invoice=invoice)
    return redirect(url_for("email.index"))
