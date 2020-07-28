from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from backend.receipts import bp
from models import requires_access_level
from models.user.constants import ACCESS_ADMIN, ACCESS_ORGANIZER
from constants import *
from .forms import ReceiptSettingsForm, TicketSettingsForm
from ext import db


@bp.route("/", methods=[GET, POST])
@login_required
@requires_access_level(ACCESS_ADMIN, ACCESS_ORGANIZER)
def index():
    settings_form = ReceiptSettingsForm()
    tickets_form = TicketSettingsForm()
    if request.method == POST:
        if settings_form.save_changes.name in request.form and settings_form.validate_on_submit():
            settings_form.save()
            flash("Receipt settings saved.")
            db.session.commit()
            return redirect(url_for("receipts.index"))
        if tickets_form.save_changes.name in request.form and tickets_form.validate_on_submit():
            tickets_form.save()
            flash("Ticket settings saved.")
            db.session.commit()
            return redirect(url_for("receipts.index"))
    return render_template("receipts/index.html", settings_form=settings_form, tickets_form=tickets_form)
