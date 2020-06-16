from flask import render_template, redirect, url_for, flash
from backend.email import bp
from constants import GET
from mailing.util import filtered_form
from models import User, Purchase, Ticket, Party, Invoice
from utilities import activation_code
from datetime import datetime, timedelta


GROUP_ERROR = "error"
NAME_TRACE = "trace"
GROUP_AUTH = "auth"
NAME_ACTIVATE_ACCOUNT = "activate_account"
NAME_RESET_PASSWORD = "reset_password"
NAME_PASSWORD_CHANGED = "password_changed"
GROUP_PURCHASE = "purchase"
NAME_PURCHASE = "purchased_tickets"
GROUP_INVOICES = "invoices"
NAME_SEND_INVOICE = "send_invoice"


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
        },
        {
            "group": GROUP_PURCHASE,
            "emails": {
                NAME_PURCHASE: "Confirmed purchase",
            }
        },
        {
            "group": GROUP_INVOICES,
            "emails": {
                NAME_SEND_INVOICE: "Invoice sent",
            }
        }
    ]
    return render_template("email/index.html", email_list=email_list)


@bp.route("/preview/<string:group>/<string:name>", methods=[GET])
def preview(group, name):
    groups = [GROUP_ERROR, GROUP_AUTH, GROUP_PURCHASE, GROUP_INVOICES]
    names = [NAME_TRACE, NAME_ACTIVATE_ACCOUNT, NAME_RESET_PASSWORD, NAME_PASSWORD_CHANGED, NAME_PURCHASE,
             NAME_SEND_INVOICE]
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
        if name == NAME_PURCHASE:
            purchase = Purchase.query.first()
            if not purchase:
                start_time = datetime.utcnow().replace(hour=22, minute=30)
                usr = User("club@test.com")
                usr.club = "Club"
                party = Party()
                party.party_id = 42
                party.name = "Amazing party"
                party.party_start_datetime = start_time
                party.party_end_datetime = start_time + timedelta(hours=5)
                party.club_owner = usr
                tickets = 3
                purchase = Purchase()
                purchase.party = party
                purchase.party_id = party.party_id
                purchase.purchase_id = 10
                purchase.ticket_price = 2500
                purchase.price = purchase.ticket_price * tickets
                purchase.first_name = "Charlie"
                purchase.last_name = "Brown"
                purchase.email = "c.brown@example.com"
                purchase.mollie_payment_id = "tr_mollieID123"
                purchase.purchase_datetime = datetime.utcnow()
                purchase.hash = purchase.set_hash()
                for i in range(tickets):
                    ticket = Ticket()
                    ticket.number = i + 1
                    purchase.tickets.append(ticket)
            return render_template(path, purchase=purchase)
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
