from flask import render_template, request, current_app, send_from_directory, flash, redirect, url_for
from flask_login import login_required
from backend.receipts import bp
from models import requires_access_level
from models.user.constants import ACCESS_ADMIN, ACCESS_ORGANIZER
from constants import *
from .forms import TestReceiptForm, ReceiptSettingsForm
import os
from ext import db


@bp.route("/", methods=[GET, POST])
@login_required
@requires_access_level(ACCESS_ADMIN, ACCESS_ORGANIZER)
def index():
    receipt_form = TestReceiptForm()
    settings_form = ReceiptSettingsForm()
    if request.method == POST:
        if receipt_form.view_receipt.name in request.form and receipt_form.validate_on_submit():
            p = receipt_form.purchase.data
            if p:
                p.generate_receipt()
                db.session.commit()
                directory = os.path.join(current_app.static_folder, RECEIPTS_FOLDER)
                return send_from_directory(directory=directory, filename=p.receipt_file_name,
                                           mimetype="application/pdf", as_attachment=True, cache_timeout=0)
            return redirect(url_for("receipts.index"))
        if settings_form.save_changes.name in request.form and settings_form.validate_on_submit():
            settings_form.save()
            flash("Receipt settings saved.")
            db.session.commit()
            return redirect(url_for("receipts.index"))
    return render_template("receipts/index.html", receipt_form=receipt_form, settings_form=settings_form)