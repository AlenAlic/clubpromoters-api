from flask import request, jsonify, g, json
from flask_login import login_required, current_user
from backend.organizer import bp
from backend.models import requires_access_level, User, Configuration, Code, Party, Purchase, Refund, Location, \
    PartyFile
from backend import db
from backend.values import *
import random
from backend.util import auth_token, datetime_python
from sqlalchemy import or_
from backend.util import upload_file, last_month_datetime
from sqlalchemy import func
from datetime import datetime
from mollie.api.client import Client
from backend.auth.email import send_activation_email


def random_code():
    return ''.join(random.sample('01234567', 6))


@bp.route('/config', methods=[GET, POST])
@login_required
@requires_access_level([AL_ORGANIZER])
def config():
    c = Configuration.query.first()
    if request.method == GET:
        return jsonify(c.json())
    if request.method == POST:
        form = json.loads(request.data)
        c.default_club_owner_commission = form["default_club_owner_commission"]
        c.default_promoter_commission = form["default_promoter_commission"]
        c.mollie_api_key = form["mollie_api_key"]
        c.test_email = form["test_email"]
        c.set_minimum_promoter_commission(form["minimum_promoter_commission"])
        c.set_administration_costs(form["administration_costs"])
        db.session.commit()
        return jsonify(c.json())


@bp.route('/upload_terms', methods=[POST])
@login_required
@requires_access_level([AL_ORGANIZER])
def upload_images():
    files = request.files
    pdf_file = upload_file(files["terms"], current_user)
    if pdf_file:
        g.config.terms = pdf_file
        db.session.commit()
    return jsonify(g.config.json())


@bp.route('/create_new_club_owner', methods=[POST])
@login_required
@requires_access_level([AL_ORGANIZER])
def create_new_club_owner():
    form = json.loads(request.data)
    account = User()
    account.club = form["club"]
    account.email = form["email"]
    account.commission = form["commission"]
    account.auth_code = auth_token()
    account.access = AL_CLUB_OWNER
    db.session.add(account)
    db.session.commit()
    send_activation_email(account)
    return OK


@bp.route('/create_new_location', methods=[POST])
@login_required
@requires_access_level([AL_ORGANIZER])
def create_new_location():
    form = json.loads(request.data)
    club_owner = User.query.filter(User.user_id == form["user_id"]).first()
    location = Location()
    location.user = club_owner
    location.name = form["name"]
    location.street = form["street"]
    location.street_number = form["street_number"]
    location.street_number_addition = form["street_number_addition"]
    location.postal_code = form["postal_code"]
    location.postal_code_letters = form["postal_code_letters"].upper()
    location.city = form["city"]
    location.maps_url = form["maps_url"]
    db.session.add(location)
    db.session.commit()
    return OK


@bp.route('/create_new_hostess', methods=[POST])
@login_required
@requires_access_level([AL_ORGANIZER])
def create_new_hostess():
    form = json.loads(request.data)
    club_owner = User.query.filter(User.user_id == form["user_id"]).first()
    account = User()
    account.email = form["email"]
    account.first_name = form["first_name"]
    account.last_name = form["last_name"]
    account.auth_code = auth_token()
    account.access = AL_HOSTESS
    account.working = True
    account.club_owner = club_owner
    db.session.add(account)
    db.session.commit()
    send_activation_email(account)
    return OK


@bp.route('/create_new_promoter', methods=[POST])
@login_required
@requires_access_level([AL_ORGANIZER])
def create_new_promoter():
    form = json.loads(request.data)
    account = User()
    account.email = form["email"]
    account.first_name = form["first_name"]
    account.last_name = form["last_name"]
    account.commission = form["commission"]
    account.code = Code.query.filter(Code.code_id == form["code_id"]).first()
    account.auth_code = auth_token()
    account.access = AL_PROMOTER
    db.session.add(account)
    db.session.commit()
    send_activation_email(account)
    return OK


@bp.route('/update_user_commission', methods=[PATCH])
@login_required
@requires_access_level([AL_ORGANIZER])
def update_user_commission():
    form = json.loads(request.data)
    account = User.query.filter(User.user_id == form["user_id"]).first()
    account.commission = form["commission"]
    db.session.commit()
    return OK


@bp.route('/users', methods=[GET])
@login_required
@requires_access_level([AL_ORGANIZER])
def users():
    u = User.query.filter(or_(User.access == AL_CLUB_OWNER, User.access == AL_PROMOTER)).all()
    return jsonify([user.json() for user in u])


@bp.route('/club_owners', methods=[GET])
@login_required
@requires_access_level([AL_ORGANIZER])
def club_owners():
    u = User.query.filter(User.access == AL_CLUB_OWNER).all()
    return jsonify([user.json() for user in u])


@bp.route('/promoters', methods=[GET])
@login_required
@requires_access_level([AL_ORGANIZER])
def promoters():
    u = User.query.filter(User.access == AL_PROMOTER).all()
    return jsonify([user.json() for user in u])


@bp.route('/codes/active', methods=[GET])
@login_required
@requires_access_level([AL_ORGANIZER])
def active_codes():
    codes = Code.query.filter(Code.active.is_(True)).order_by(Code.code).all()
    return jsonify([c.json() for c in codes])


@bp.route('/codes/inactive', methods=[GET])
@login_required
@requires_access_level([AL_ORGANIZER])
def inactive_codes():
    codes = Code.query.filter(Code.active.is_(False)).order_by(Code.code).all()
    return jsonify([c.json() for c in codes])


@bp.route('/codes', methods=[POST])
@login_required
@requires_access_level([AL_ORGANIZER])
def create_codes():
    form = json.loads(request.data)
    all_codes = [f"{n:06}" for n in range(1, 1000000)]
    existing_codes = db.session.query(Code.code).all()
    remaining_codes = list(set(all_codes) - set(existing_codes))
    new_codes = random.sample(remaining_codes, int(form["num"]))
    for code in new_codes:
        c = Code()
        c.code = code
        db.session.add(c)
    db.session.commit()
    return OK


@bp.route('/assign_code_to_promoter', methods=[PATCH])
@login_required
@requires_access_level([AL_ORGANIZER])
def assign_code_to_promoter():
    form = json.loads(request.data)
    account = User.query.filter(User.user_id == form["user_id"]).first()
    c = Code.query.filter(Code.code_id == form["code_id"]).first()
    account.code = c
    db.session.commit()
    return OK


@bp.route('/codes/deactivate/<int:code_id>', methods=[PATCH])
@login_required
@requires_access_level([AL_ORGANIZER])
def deactivate(code_id):
    code = Code.query.filter(Code.code_id == code_id).first()
    code.deactivate()
    db.session.commit()
    return OK


@bp.route('/create_new_party', methods=[POST])
@login_required
@requires_access_level([AL_ORGANIZER])
def create_new_party():
    form = json.loads(request.data)
    club_owner = User.query.filter(User.user_id == form["club"]).first()
    party = Party()
    party.name = form["name"]
    party.location_id = form["location"]
    party.party_start_datetime = datetime_python(form["start_date"])
    party.party_end_datetime = datetime_python(form["end_date"])
    if "description" in form:
        party.description = form["description"]
    party.num_available_tickets = form["number_of_tickets"]
    party.set_ticket_price(form["ticket_price"])
    party.status = NORMAL
    party.club_owner_commission = form["club_owner_commission"]
    party.club_owner = club_owner
    party.promoter_commission = form["promoter_commission"]
    for idx, file_id in enumerate(form["images"]):
        party_file = PartyFile()
        party_file.party = party
        party_file.file_id = file_id
        party_file.order = idx
    party.logo_id = form["logo"]
    party.interval = form["interval"]
    db.session.add(party)
    db.session.commit()
    return OK


@bp.route('/edit_party/<int:party_id>', methods=[POST])
@login_required
@requires_access_level([AL_ORGANIZER])
def edit_party(party_id):
    form = json.loads(request.data)
    party = Party.query.filter(Party.party_id == party_id).first()
    if party:
        party.name = form["name"]
        party.num_available_tickets = form["number_of_tickets"]
        party.set_ticket_price(form["ticket_price"])
        party.club_owner_commission = form["club_owner_commission"]
        party.promoter_commission = form["promoter_commission"]
        db.session.commit()
        return OK
    return BAD_REQUEST


@bp.route('/inactive_parties', methods=[GET])
@login_required
@requires_access_level([AL_ORGANIZER])
def inactive_parties():
    parties = Party.query.filter(Party.is_active.is_(False), Party.party_end_datetime > datetime.utcnow())\
        .order_by(Party.party_start_datetime).all()
    return jsonify([p.json() for p in parties])


@bp.route('/activate_party/<int:party_id>', methods=[PATCH])
@login_required
@requires_access_level([AL_ORGANIZER])
def activate_party(party_id):
    party = Party.query.filter(Party.party_id == party_id).first()
    party.is_active = True
    db.session.commit()
    return OK


@bp.route('/deactivate_party/<int:party_id>', methods=[PATCH])
@login_required
@requires_access_level([AL_ORGANIZER])
def deactivate_party(party_id):
    party = Party.query.filter(Party.party_id == party_id).first()
    party.is_active = False
    db.session.commit()
    return OK


@bp.route('/past_parties', methods=[GET])
@login_required
@requires_access_level([AL_ORGANIZER])
def past_parties():
    parties = Party.query.filter(Party.is_active.is_(True), Party.party_end_datetime < datetime.utcnow())\
        .order_by(Party.party_start_datetime).all()
    return jsonify([p.json() for p in parties])


def parties_list(year, month):
    last_month = last_month_datetime(year, month)
    # party = Party.query.filter(Party.is_active.is_(True), Party.party_end_datetime < datetime.now(),
    #                            func.month(Party.party_end_datetime) == func.month(last_month),
    #                            func.year(Party.party_end_datetime) == func.year(last_month)).all()
    party = Party.query.filter(Party.is_active.is_(True),
                               func.month(Party.party_end_datetime) == func.month(last_month),
                               func.year(Party.party_end_datetime) == func.year(last_month)).all()
    return [p.json() for p in party]


@bp.route('/party_income/<int:year>/<int:month>', methods=[GET])
@login_required
@requires_access_level([AL_ORGANIZER])
def party_income(year, month):
    return jsonify(parties_list(year, month))


def purchases_list(year, month):
    last_month = last_month_datetime(year, month)
    purchase = Purchase.query.filter(Purchase.purchase_datetime < datetime.now(),
                                     func.month(Purchase.purchase_datetime) == func.month(last_month),
                                     func.year(Purchase.purchase_datetime) == func.year(last_month)).all()
    return [p.json() for p in purchase]


@bp.route('/purchase/<int:year>/<int:month>', methods=[GET])
@login_required
@requires_access_level([AL_ORGANIZER])
def purchases(year, month):
    return jsonify(purchases_list(year, month))


@bp.route('/refund', methods=[POST])
@login_required
@requires_access_level([AL_ORGANIZER])
def refund():
    mollie_client = Client()
    mollie_client.set_api_key(g.mollie)

    form = json.loads(request.data)
    purchase_id = form["purchase_id"]
    amount = form["amount"]
    mollie_value = '{:,.2f}'.format(float(amount))

    purchase = Purchase.query.filter(Purchase.purchase_id == purchase_id).first()
    mollie_id = purchase.mollie_payment_id
    payment = mollie_client.payments.get(mollie_id)

    if payment is not None:
        ref = Refund()
        ref.set_price(float(mollie_value))
        ref.purchase = purchase
        db.session.add(ref)
        db.session.commit()

        if payment.can_be_refunded() and 1.0 <= float(amount) <= float(payment.amount_remaining['value']):
            data = {
                'amount': {'value': mollie_value, 'currency': 'EUR'},
                'description': f'test {datetime.now().strftime("%d-%m-%Y %H:%M:%S")}'
            }
            r = mollie_client.payment_refunds.with_parent_id(mollie_id).create(data)
            ref.mollie_refund_id = r["id"]
            db.session.commit()
            return jsonify(purchase.json())
        else:
            db.session.delete(ref)
            db.session.commit()
            return BAD_REQUEST
    return NOT_FOUND


@bp.route('/commissions/<int:year>/<int:month>', methods=[GET])
@login_required
@requires_access_level([AL_ORGANIZER])
def commissions(year, month):
    last_month = last_month_datetime(year, month)
    purchase = Purchase.query.filter(Purchase.purchase_datetime < datetime.now(),
                                     func.month(Purchase.purchase_datetime) == func.month(last_month),
                                     func.year(Purchase.purchase_datetime) == func.year(last_month)).all()
    promoters = list(set([p.promoter_id for p in purchase if p.promoter_id is not None]))
    club_owners = list(set([p.party.club_owner_id for p in purchase if p.party.club_owner_id is not None]))
    u = User.query.filter(User.user_id.in_(promoters + club_owners), User.is_active.is_(True)).all()
    return jsonify([user.commissions_json(purchase) for user in u])


# @bp.route('/party_images', methods=['GET', 'POST'])
# @login_required
# @requires_access_level([ACCESS[ORGANIZER]])
# def party_images():
#     upload_form = UploadImagesForm()
#     if request.method == "POST":
#         if upload_form.validate_on_submit():
#             club_owner = User.query.filter(User.user_id == upload_form.club_owner.data).first()
#             if upload_form.logo.name in request.files:
#                 upload_file(request.files[upload_form.logo.name], club_owner, LOGO)
#             if upload_form.image.name in request.files:
#                 upload_file(request.files[upload_form.image.name], club_owner, IMAGE)
#             return redirect(url_for('organizer.party_images'))
#     return render_template('organizer/party_images.html', upload_form=upload_form)
# 
# 
# @bp.route('/party_template', methods=['GET', 'POST'])
# @login_required
# @requires_access_level([ACCESS[ORGANIZER]])
# @page_inactive
# def party_template():
#     return render_template('organizer/party_template.html')
