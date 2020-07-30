from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from backend.demo import bp
from models import requires_access_level, User, Code, Location, File
from models.user.constants import ACCESS_ADMIN, ACCESS_ORGANIZER, ACCESS_CLUB_OWNER, ACCESS_HOSTESS, ACCESS_PROMOTER
from ext import db
from constants import *
from .forms import CreateDemoClubsForm, CreateCurrentPartiesForm, CreatePastPartiesForm
import os
import shutil
from time import time
from .data import CLUBS, PROMOTERS
from backend.testing.forms import TestEmailForm


@bp.route('/', methods=[GET, POST])
@login_required
@requires_access_level(ACCESS_ADMIN, ACCESS_ORGANIZER)
def index():
    test_email_form = TestEmailForm()
    clubs = User.query.filter(User.club.in_([c["name"] for c in CLUBS])).all()
    promoters = User.query.filter(User.first_name.in_([c["first_name"] for c in PROMOTERS]),
                                  User.last_name == "Test").all()
    demo_club_form = CreateDemoClubsForm()
    create_current_parties_form = CreateCurrentPartiesForm()
    create_past_parties_form = CreatePastPartiesForm()
    if request.method == POST:
        if test_email_form.save_email.name in request.form and test_email_form.validate_on_submit():
            test_email_form.save()
            if test_email_form.test_email.data:
                flash("Testing e-mail saved.")
            else:
                flash("Testing e-mail cleared.")
            db.session.commit()
            return redirect(url_for("demo.index"))
        if demo_club_form.create_clubs.name in request.form and demo_club_form.validate_on_submit():
            for data in CLUBS:
                club = User.query.filter(User.club == data["name"]).first()
                if not club:
                    club_owner = User(
                        email=f"organizer@{data['path']}.com",
                        password=demo_club_form.password.data
                    )
                    club_owner.club = data["name"]
                    club_owner.access = ACCESS_CLUB_OWNER
                    club_owner.business_entity = True
                    club_owner.is_active = True
                    club_owner.commission = data["commission"]
                    club_owner.iban = data["iban"]
                    club_owner.iban_verified = True
                    club_owner.invoice_legal_name = data["invoice"]["legal_name"]
                    club_owner.street = data["invoice"]["street"]
                    club_owner.street_number = data["invoice"]["street_number"]
                    club_owner.postal_code = data["invoice"]["postal_code"]
                    club_owner.postal_code_letters = data["invoice"]["postal_code_letters"]
                    club_owner.city = data["invoice"]["city"]
                    club_owner.country = data["invoice"]["country"]
                    club_owner.invoice_kvk_number = data["invoice"]["kvk"]
                    club_owner.invoice_vat_number = data["invoice"]["vat"]
                    club_owner.accepted_terms = True
                    db.session.add(club_owner)
                    db.session.flush()
                    directory = os.path.join(current_app.uploads_folder, f"{club_owner.user_id}")
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    for img in range(1, 8):
                        filename = f"{img}.jpg"
                        dest = os.path.join(directory, f"{time()}.jpg")
                        shutil.copyfile(os.path.join(
                            current_app.static_folder, "testing_images", data["path"], filename),
                            dest
                        )
                        f = File()
                        f.name = filename
                        f.path = dest
                        f.user = club_owner
                        f.logo = img in data["logos"]
                    location = Location()
                    location.name = data["location"]["name"]
                    location.street = data["location"]["street"]
                    location.street_number = data["location"]["street_number"]
                    location.postal_code = data["location"]["postal_code"]
                    location.postal_code_letters = data["location"]["postal_code_letters"]
                    location.city = data["location"]["city"]
                    location.maps_url = data["location"]["maps_url"]
                    location.user = club_owner
                    db.session.add(location)
                    hostess = User(
                        email=f"hostess@{data['path']}.com",
                        password=demo_club_form.password.data
                    )
                    hostess.first_name = "Anne"
                    hostess.last_name = "Test"
                    hostess.access = ACCESS_HOSTESS
                    hostess.is_active = True
                    hostess.working = True
                    hostess.club_owner = club_owner
                    db.session.add(hostess)
                db.session.commit()
            for data in PROMOTERS:
                promoter = User.query.filter(User.first_name == data["first_name"],
                                             User.last_name == data["last_name"]).first()
                if not promoter:
                    promoter = User(
                        email=f"{data['first_name'].lower()}_{data['last_name'].lower()}@promoter.com",
                        password=demo_club_form.password.data
                    )
                    promoter.first_name = data["first_name"]
                    promoter.last_name = data["last_name"]
                    promoter.access = ACCESS_PROMOTER
                    promoter.is_active = True
                    promoter.commission = data["commission"]
                    promoter.iban = data["iban"]
                    promoter.iban_verified = True
                    promoter.invoice_legal_name = data["invoice"]["legal_name"]
                    promoter.street = data["invoice"]["street"]
                    promoter.street_number = data["invoice"]["street_number"]
                    promoter.postal_code = data["invoice"]["postal_code"]
                    promoter.postal_code_letters = data["invoice"]["postal_code_letters"]
                    promoter.city = data["invoice"]["city"]
                    promoter.country = data["invoice"]["country"]
                    promoter.business_entity = data["business_entity"]
                    if promoter.business_entity:
                        promoter.invoice_kvk_number = data["invoice"]["kvk"]
                        promoter.invoice_vat_number = data["invoice"]["vat"]
                    promoter.accepted_terms = True
                    db.session.add(promoter)
                    code = Code()
                    code.code = data["code"]
                    code.user = promoter
                db.session.commit()
            return redirect(url_for('demo.index'))
        if create_current_parties_form.create_current_parties.name in request.form \
                and create_current_parties_form.validate_on_submit():
            create_current_parties_form.save(clubs)
            db.session.commit()
            flash(f"Added new parties starting today.")
            return redirect(url_for("demo.index"))
        if create_past_parties_form.create_past_parties.name in request.form \
                and create_past_parties_form.validate_on_submit():
            create_past_parties_form.save(clubs)
            db.session.commit()
            flash(f"Added new parties up to today.")
            return redirect(url_for("demo.index"))
    status = {
        "clubs": clubs,
        "clubs_created": len(clubs) == len(CLUBS),
        "promoters": promoters,
    }
    return render_template('demo/index.html', status=status, test_email_form=test_email_form,
                           demo_club_form=demo_club_form, create_current_parties_form=create_current_parties_form,
                           create_past_parties_form=create_past_parties_form)
