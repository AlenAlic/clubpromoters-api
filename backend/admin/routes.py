from flask import jsonify, json, request, redirect, url_for, flash, current_app, g
from flask_login import login_user, logout_user, login_required, current_user
from backend.admin import bp
from backend.models import requires_access_level, User, Code, Party, Purchase, Ticket, File, Refund
from backend.values import *
from backend import db
from backend.auth.email import send_activation_email
from backend.util import auth_token
import random
import string
from datetime import datetime, timezone, timedelta
import shutil
import os


@bp.route('/switch', methods=[GET], defaults={"user_id": None})
@bp.route('/switch/<int:user_id>', methods=[POST])
@login_required
@requires_access_level([AL_ADMIN])
def switch(user_id):
    if request.method == GET:
        users = User.query.filter(User.access != AL_ADMIN, User.is_active.is_(True)).all()
        return jsonify([{"text": u.email, "value": u.user_id} for u in users])
    if request.method == POST:
        u = User.query.filter(User.access != AL_ADMIN, User.is_active.is_(True), User.user_id == user_id).first()
        if u is not None:
            return jsonify(u.get_auth_token())
        else:
            return BAD_REQUEST


@bp.route('/has_organizer', methods=[GET])
@login_required
@requires_access_level([AL_ADMIN])
def has_organizer():
    if request.method == GET:
        users = User.query.filter(User.access == AL_ORGANIZER).count()
        return jsonify(users > 0)


@bp.route('/create_organizer_account', methods=[POST])
@login_required
def setup():
    form = json.loads(request.data)
    organizer = User()
    organizer.email = form["email"]
    organizer.access = AL_ORGANIZER
    organizer.auth_code = auth_token()
    db.session.add(organizer)
    db.session.commit()
    send_activation_email(organizer)
    return OK


# def random_password():
#     allowed_chars = string.ascii_letters + '0123456789'
#     return ''.join(random.sample(allowed_chars, 16))
#
#
# @bp.route('/dashboard', methods=['GET'])
# @login_required
# def dashboard():
#     return render_template('admin/dashboard.html')
#
#
# @bp.route('/users', methods=['GET'])
# @login_required
# def users():
#     return render_template('admin/users.html')
#
#
# @bp.route('/setup', methods=['GET', 'POST'])
# @login_required
# def setup():
#     create_form = CreateOrganizerAccountFrom()
#     organizer = User.query.filter(User.access == ACCESS[ORGANIZER]).first()
#     if request.method == "POST":
#         if create_form.validate_on_submit():
#             organizer = User()
#             organizer.username = ORGANIZER
#             organizer.email = create_form.email.data
#             organizer.access = ACCESS[ORGANIZER]
#             organizer.activation_code = activation_code()
#             db.session.add(organizer)
#             db.session.commit()
#             send_activation_email(organizer)
#             flash("Organizer account created.")
#             return redirect(url_for('self_admin.setup'))
#     return render_template('admin/setup.html', create_form=create_form, organizer=organizer)
#
#
# @bp.route('/test_data', methods=['GET', 'POST'])
# @login_required
# def test_data():
#     test_values = {
#         "tickets": 50,
#         "ticket_price": 25,
#         "purchase": {
#             "paid_tickets": [2, 3, 5, 6, 1, 3, 4, 7, 3, 2, 1],
#             "cancelled_tickets": [2, 3, 5, 1]
#         },
#         "code_base": 100000,
#         "refund_border": 4
#     }
#     test_config = {
#         "organizer": User.query.filter(User.access == ACCESS[ORGANIZER]).first(),
#         "club_owners": 4,
#         "promoters": 10,
#         "codes": 15,
#         "parties": 8,
#         "purchases": Purchase.query.all(),
#         "refunds": Refund.query.all()
#     }
#     test_check = {
#         "organizer": test_config["organizer"] is not None,
#         "club_owners": len(User.query.filter(User.access == ACCESS[CLUB_OWNER]).all()) >= test_config["club_owners"],
#         "promoters": len(User.query.filter(User.access == ACCESS[PROMOTER]).all()) >= test_config["promoters"],
#         "codes": len(Code.query.all()) >= test_config["codes"],
#         "parties": len(Party.query.all()) >= test_config["parties"],
#         "purchases": len(test_config["purchases"]) > 0,
#         "refunds": len(test_config["refunds"]) > 0
#     }
#     if request.method == "POST":
#         if "reset" in request.form:
#             site_users = User.query.filter(User.access != ACCESS[ADMIN]).all()
#             for u in site_users:
#                 db.session.delete(u)
#             Refund.query.delete()
#             File.query.delete()
#             directory = os.path.join(current_app.static_folder, UPLOAD_FOLDER)
#             if os.path.exists(directory):
#                 shutil.rmtree(directory)
#                 os.makedirs(directory)
#             Ticket.query.delete()
#             Purchase.query.delete()
#             Code.query.delete()
#             Party.query.delete()
#             db.session.commit()
#             flash("Test data reset.")
#         if "organizer" in request.form:
#             if not test_check["organizer"]:
#                 organizer = User()
#                 organizer.username = ORGANIZER
#                 organizer.email = "organizer@test.com"
#                 organizer.access = ACCESS[ORGANIZER]
#                 organizer.is_active = True
#                 organizer.set_password(random_password())
#                 db.session.add(organizer)
#                 db.session.commit()
#                 flash(f"Added {ORGANIZER} account.", "success")
#             else:
#                 flash(f"There already is an {ORGANIZER} account.", "warning")
#         if "club_owners" in request.form:
#             if not test_check["club_owners"]:
#                 for i in range(test_config["club_owners"]):
#                     club_owner = User()
#                     club_owner.username = f"{CLUB_OWNER}{i}"
#                     club_owner.email = f"{CLUB_OWNER}{i}@test.com"
#                     club_owner.access = ACCESS[CLUB_OWNER]
#                     club_owner.is_active = True
#                     club_owner.set_password(random_password())
#                     club_owner.commission = g.config.default_club_owner_commission
#                     db.session.add(club_owner)
#                     hostess = User()
#                     hostess.club_owner = club_owner
#                     hostess.username = f"{HOSTESS}{i}"
#                     hostess.email = f"{HOSTESS}{i}@test.com"
#                     hostess.access = ACCESS[HOSTESS]
#                     hostess.is_active = True
#                     hostess.set_password(random_password())
#                     db.session.add(hostess)
#                 db.session.commit()
#                 flash(f"Added testing {CLUB_OWNER} (and {HOSTESS}') accounts.", "success")
#             else:
#                 flash(f"The {CLUB_OWNER} (and {HOSTESS}') accounts for testing have already been created.", "warning")
#         if "codes" in request.form:
#             if not test_check["codes"]:
#                 for i in range(test_config["codes"]):
#                     db.session.add(Code(code=f"{test_values['code_base'] + i}"))
#                 db.session.commit()
#                 flash("Added testing Codes.", "success")
#             else:
#                 flash("The testing Codes have already been created.", "warning")
#         if "promoters" in request.form:
#             if not test_check["promoters"] or test_check["codes"]:
#                 for i in range(test_config["promoters"]):
#                     promoter = User()
#                     promoter.username = f"{PROMOTER}{i}"
#                     promoter.email = f"{PROMOTER}{i}@test.com"
#                     promoter.access = ACCESS[PROMOTER]
#                     promoter.is_active = True
#                     promoter.set_password(random_password())
#                     promoter.code = Code.query.filter(Code.user_id.is_(None)).first()
#                     promoter.commission = g.config.default_promoter_commission
#                     db.session.add(promoter)
#                 db.session.commit()
#                 flash(f"Added testing {PROMOTER} accounts.", "success")
#             else:
#                 flash(f"The {PROMOTER} accounts for testing have already been created.", "warning")
#         if "parties" in request.form:
#             if not test_check["parties"] or test_check["club_owners"]:
#                 club_owner = User.query.filter(User.access == ACCESS[CLUB_OWNER]).first()
#                 for i in range(test_config["parties"]):
#                     party = Party()
#                     party.title = f"Party{i}"
#                     start_date = datetime.now().replace(tzinfo=timezone.utc, hour=23, minute=0,
#                                                         second=0, microsecond=0) + (i % 3 - 1) * timedelta(days=8 * i)
#                     start_date = start_date - timedelta(days=2)
#                     party.party_start_datetime = start_date
#                     party.party_end_datetime = start_date + timedelta(hours=5)
#                     party.num_available_tickets = test_values["tickets"]
#                     party.set_ticket_price(test_values["ticket_price"] + 5 * i)
#                     party.status = NORMAL
#                     party.club_owner = club_owner
#                     party.image = PLACEHOLDER_URL
#                     party.logo = PLACEHOLDER_URL
#                     party.is_active = True
#                     db.session.add(party)
#                 db.session.commit()
#                 flash("Added testing Parties.", "success")
#             else:
#                 flash("The testing Parties have already been created.", "warning")
#         if "purchases" in request.form:
#             if not test_check["purchases"] or test_check["parties"]:
#                 parties = Party.query.all()
#                 for party in parties:
#                     for i in test_values["purchase"]["paid_tickets"]:
#                         c = Code.query.filter(Code.code == f"{test_values['code_base'] + i}").first()
#                         purchase = Purchase(party=party, email="test@test.com", name="Test Tester",
#                                             status=STATUS_PAID, code=c, promoter=c.user,
#                                             promoter_commission=c.user.commission,
#                                             club_owner_commission=party.club_owner.commission)
#                         purchase.set_price(party.get_ticket_price() * i)
#                         for j in range(i):
#                             purchase.tickets.append(Ticket(number=j+1, used=j % 3 == 0, denied_entry=j % 4 != 0))
#                         db.session.add(purchase)
#                         db.session.flush()
#                         purchase.set_hash()
#                         db.session.commit()
#                     for i in test_values["purchase"]["paid_tickets"]:
#                         c = Code.query.filter(Code.code == f"{test_values['code_base'] + i}").first()
#                         purchase = Purchase(party=party, email="test@test.com", name="Test Tester",
#                                             status=STATUS_CANCELED, code=c, promoter=c.user,
#                                             promoter_commission=c.user.commission,
#                                             club_owner_commission=party.club_owner.commission)
#                         purchase.set_price(party.get_ticket_price() * i)
#                         for j in range(i):
#                             purchase.tickets.append(Ticket(number=j+1))
#                         db.session.add(purchase)
#                         db.session.flush()
#                         purchase.set_hash()
#                         db.session.commit()
#                 flash("Added testing Purchases.", "success")
#             else:
#                 flash("The testing Purchases have already been created.", "warning")
#         if "refunds" in request.form:
#             if not test_check["refunds"] or test_check["purchases"]:
#                 parties = Party.query.all()
#                 for party in parties:
#                     for purchase in [p for p in party.purchases if p.status == STATUS_PAID]:
#                         tickets = [t for t in purchase.tickets]
#                         tickets[0].refunded = True
#                         if len(tickets) > test_values["refund_border"]:
#                             tickets[test_values["refund_border"]].refunded = True
#                         r = 2 if len(tickets) > test_values["refund_border"] else 1
#                         refund = Refund()
#                         refund.set_price(r * purchase.get_ticket_price())
#                         refund.purchase = purchase
#                         db.session.add(refund)
#                 db.session.commit()
#                 flash("Added testing Refunds.", "success")
#             else:
#                 flash("The testing Refunds have already been created.", "warning")
#         return redirect(url_for('self_admin.test_data'))
#     return render_template('admin/test_data.html', test_check=test_check)
#
#
# @bp.route('/switch_organizer', methods=['GET'])
# @login_required
# def switch_organizer():
#     user = User.query.filter(User.access == ACCESS[ORGANIZER], User.is_active.is_(True),
#                              User.password_hash.isnot(None)).first()
#     if user is not None:
#         logout_user()
#         login_user(user)
#     else:
#         flash(f'{ORGANIZER} account is not available.')
#     return redirect(url_for('main.index'))
#
#
# @bp.route('/switch_user', methods=['GET', 'POST'])
# @login_required
# def switch_user():
#     if request.method == "POST":
#         user = User.query.filter(User.access > ACCESS[ORGANIZER], User.is_active.is_(True),
#                                  User.password_hash.isnot(None), User.user_id == request.form["user"]).first()
#         if user is not None:
#             logout_user()
#             login_user(user)
#             return redirect(url_for('main.index'))
#     switchable_users = User.query.filter(User.access > ACCESS[ORGANIZER], User.is_active.is_(True),
#                                          User.password_hash.isnot(None)).all()
#     return render_template('admin/switch_user.html', users=switchable_users)
#
#
# @bp.route('/test_emails', methods=['GET', "POST"])
# @login_required
# def test_emails():
#     email = {
#         "activate_account": "Account activation",
#         "purchased_tickets": "Confirmation of ticket purchase"
#     }
#     txt_preview, html_preview = None, None
#     if request.method == "POST":
#         if "activate_account" in request.form:
#             token = current_user.get_reset_password_token(expires_in=86400)
#             txt_preview = render_template('email/activate_account.txt', user=current_user, token=token)
#             html_preview = render_template('email/activate_account.html', user=current_user, token=token)
#         if "purchased_tickets" in request.form:
#             purchase = Purchase.query.filter(Purchase.status == STATUS_PAID).first()
#             if purchase is not None:
#                 txt_preview = render_template('email/purchased_tickets.txt', purchase=purchase)
#                 html_preview = render_template('email/purchased_tickets.html', purchase=purchase)
#             else:
#                 flash(f"There are no paid purchases", "warning")
#     return render_template('admin/test_emails.html', email=email, txt_preview=txt_preview, html_preview=html_preview)
