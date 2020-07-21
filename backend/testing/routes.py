from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from backend.testing import bp
from models import requires_access_level
from models.user.constants import ACCESS_ADMIN, ACCESS_ORGANIZER
from ext import db
from constants import GET, POST
from .forms import TestEmailForm


@bp.route('/', methods=[GET, POST])
@login_required
@requires_access_level(ACCESS_ADMIN, ACCESS_ORGANIZER)
def index():
    test_email_form = TestEmailForm()
    if request.method == POST:
        if test_email_form.save_email.name in request.form and test_email_form.validate_on_submit():
            test_email_form.save()
            if test_email_form.test_email.data:
                flash("Testing e-mail saved.")
            else:
                flash("Testing e-mail cleared.")
            db.session.commit()
            return redirect(url_for("testing.index"))
    return render_template('testing/index.html', test_email_form=test_email_form)
