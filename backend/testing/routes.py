from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from backend.testing import bp
from models import requires_access_level, User, Code
from models.user.constants import  ACCESS_ADMIN, ACCESS_ORGANIZER, ACCESS_CLUB_OWNER, ACCESS_HOSTESS, ACCESS_PROMOTER
from ext import db
import random
from constants import *
from models.configuration import config
from .forms import CreateTestAccountsForm, TestEmailForm


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
    if request.method == POST:
        if test_accounts_form.create_accounts.name in request.form and test_accounts_form.validate_on_submit():
            if test_accounts_form.club_owners.data or test_accounts_form.promoters.data:
                if test_accounts_form.club_owners.name in request.form:
                    count = User.query.filter(User.access == ACCESS_CLUB_OWNER).count() + 1
                    for i in range(count, count + test_accounts_form.number.data):
                        club_owner = User()
                        club_owner.username = f"{CLUB_OWNER}{i}"
                        club_owner.email = f"{CLUB_OWNER}{i}@test.com"
                        club_owner.access = ACCESS_CLUB_OWNER
                        club_owner.is_active = True
                        club_owner.set_password("test")
                        club_owner.commission = conf.default_club_owner_commission
                        db.session.add(club_owner)
                        hostess = User()
                        hostess.club_owner = club_owner
                        hostess.username = f"{HOSTESS}{i}"
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
                        promoter.username = f"{PROMOTER}{i}"
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
    data = {
        "club_owners": User.query.filter(User.access == ACCESS_CLUB_OWNER).all(),
        "promoters": User.query.filter(User.access == ACCESS_PROMOTER).all(),
    }
    return render_template('testing/index.html',
                           test_accounts_form=test_accounts_form, test_email_form=test_email_form, data=data)
