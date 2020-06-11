from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from backend.invoices import bp
from models import requires_access_level
from models.user.constants import ACCESS_ADMIN, ACCESS_ORGANIZER
from constants import *
from .forms import InvoiceSettingsForm
from ext import db


@bp.route("/", methods=[GET, POST])
@login_required
@requires_access_level(ACCESS_ADMIN, ACCESS_ORGANIZER)
def index():
    settings_form = InvoiceSettingsForm()
    if request.method == POST:
        if settings_form.save_changes.name in request.form and settings_form.validate_on_submit():
            settings_form.save()
            flash("Invoice settings saved.")
            db.session.commit()
            return redirect(url_for("invoices.index"))
    return render_template("invoices/index.html", settings_form=settings_form)
