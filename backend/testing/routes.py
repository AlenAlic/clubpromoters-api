from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from backend.testing import bp
from models import requires_access_level, User, Code, Location, File
from models.user.constants import  ACCESS_ADMIN, ACCESS_ORGANIZER, ACCESS_CLUB_OWNER, ACCESS_HOSTESS, ACCESS_PROMOTER
from ext import db
import random
from constants import *
from models.configuration import config
from .forms import CreateTestAccountsForm, TestEmailForm, TestPartyForm
import os
import shutil
from time import time


CLUB_OWNER = "ClubOwner"
HOSTESS = "Hostess"
PROMOTER = "Promoter"


@bp.route('/', methods=[GET, POST])
@login_required
@requires_access_level(ACCESS_ADMIN, ACCESS_ORGANIZER)
def index():
    conf = config()
    test_accounts_form = CreateTestAccountsForm()
    test_email_form = TestEmailForm()
    test_party_form = TestPartyForm()
    if request.method == POST:
        if test_accounts_form.create_accounts.name in request.form and test_accounts_form.validate_on_submit():
            if test_accounts_form.club_owners.data or test_accounts_form.promoters.data:
                if test_accounts_form.club_owners.name in request.form:
                    count = User.query.filter(User.access == ACCESS_CLUB_OWNER).count() + 1
                    for i in range(count, count + test_accounts_form.number.data):
                        club_owner = User()
                        club_owner.club = f"Club {i}"
                        club_owner.username = f"{CLUB_OWNER}{i}"
                        club_owner.email = f"{CLUB_OWNER}{i}@test.com"
                        club_owner.access = ACCESS_CLUB_OWNER
                        club_owner.business_entity = True
                        club_owner.is_active = True
                        club_owner.set_password("test")
                        club_owner.commission = conf.default_club_owner_commission
                        db.session.add(club_owner)
                        db.session.flush()
                        directory = os.path.join(current_app.static_folder, UPLOAD_FOLDER, f"{club_owner.user_id}")
                        if not os.path.exists(directory):
                            os.makedirs(directory)
                        for img in range(1, 10):
                            filename = f"{img}.jpg"
                            dest = os.path.join(directory, f"{time()}.jpg")
                            shutil.copyfile(os.path.join(current_app.static_folder, "testing_images", filename), dest)
                            f = File()
                            f.name = filename
                            f.path = dest
                            f.user = club_owner
                            f.logo = img == 3 or img == 7
                        location = Location()
                        location.name = f"Loc {i}"
                        location.street = "Street"
                        location.street_number = 42
                        location.postal_code = 1234
                        location.postal_code_letters = "AB"
                        location.city = "Amsterdam"
                        location.maps_url = """https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d77979.65162740376!2
                        d4.833921041898723!3d52.35474979518866!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x47c63
                        fb5949a7755%3A0x6600fd4cb7c0af8d!2sAmsterdam!5e0!3m2!1snl!2snl!4v1591306320734!5m2!1snl!2snl"""
                        location.user = club_owner
                        db.session.add(location)
                        hostess = User()
                        hostess.club_owner = club_owner
                        hostess.first_name = f"{HOSTESS}{i}"
                        hostess.last_name = "Test"
                        hostess.email = f"{HOSTESS}{i}@test.com"
                        hostess.access = ACCESS_HOSTESS
                        hostess.is_active = True
                        hostess.set_password("test")
                        db.session.add(hostess)
                    db.session.commit()
                    flash(f"Added {test_accounts_form.number.data} testing {CLUB_OWNER} (and {HOSTESS}') accounts.",
                          "success")
                if test_accounts_form.promoters.name in request.form:
                    all_codes = [f"{n:06}" for n in range(1, 1000000)]
                    existing_codes = db.session.query(Code.code).all()
                    remaining_codes = list(set(all_codes) - set(existing_codes))
                    new_codes = random.sample(remaining_codes, test_accounts_form.number.data)
                    for code in new_codes:
                        c = Code()
                        c.code = code
                        db.session.add(c)
                    count = User.query.filter(User.access == ACCESS_PROMOTER).count() + 1
                    for i in range(count, count + test_accounts_form.number.data):
                        promoter = User()
                        promoter.first_name = f"{PROMOTER}{i}"
                        promoter.last_name = "Test"
                        promoter.email = f"{PROMOTER}{i}@test.com"
                        promoter.access = ACCESS_PROMOTER
                        promoter.is_active = True
                        promoter.set_password("test")
                        promoter.code = Code.query.filter(Code.user_id.is_(None)).first()
                        promoter.commission = conf.default_promoter_commission
                        db.session.add(promoter)
                    db.session.commit()
                    flash(f"Added {test_accounts_form.number.data} testing {PROMOTER} accounts.", "success")
                return redirect(url_for('testing.index'))
            flash(f"Please select a type of account to add", "warning")
        if test_email_form.save_email.name in request.form and test_email_form.validate_on_submit():
            test_email_form.save()
            if test_email_form.test_email.data:
                flash("Testing e-mail saved.")
            else:
                flash("Testing e-mail cleared.")
            db.session.commit()
            return redirect(url_for("testing.index"))
        if test_party_form.create_parties.name in request.form and test_party_form.validate_on_submit():
            test_party_form.save()
            db.session.commit()
            flash(f"Added {test_party_form.number.data} parties for {test_party_form.club_owner.data.club}")
            return redirect(url_for("testing.index"))
    data = {
        "club_owners": User.query.filter(User.access == ACCESS_CLUB_OWNER).all(),
        "promoters": User.query.filter(User.access == ACCESS_PROMOTER).all(),
    }
    return render_template('testing/index.html',
                           test_accounts_form=test_accounts_form, test_email_form=test_email_form,
                           test_party_form=test_party_form, data=data)
