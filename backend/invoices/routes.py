from flask import render_template, request, current_app, send_from_directory, flash, redirect, url_for
from flask_login import login_required
from backend.invoices import bp
from models import requires_access_level
from models.user.constants import ACCESS_ADMIN, ACCESS_ORGANIZER
from constants import *
from .forms import TestInvoiceForm, InvoiceSettingsForm
import os
from ext import db


@bp.route("/", methods=[GET, POST])
@login_required
@requires_access_level(ACCESS_ADMIN, ACCESS_ORGANIZER)
def index():
    invoice_form = TestInvoiceForm()
    settings_form = InvoiceSettingsForm()
    if request.method == POST:
        if invoice_form.view_invoice.name in request.form and invoice_form.validate_on_submit():
            p = invoice_form.purchase.data
            p.generate_invoice()
            db.session.commit()
            directory = os.path.join(current_app.static_folder, UPLOAD_FOLDER)
            return send_from_directory(directory=directory, filename=p.invoice_file_name, mimetype="application/pdf",
                                       as_attachment=True, cache_timeout=0)
        if settings_form.save_changes.name in request.form and settings_form.validate_on_submit():
            settings_form.save()
            flash("Invoice settings saved.")
            db.session.commit()
            return redirect(url_for("invoices.index"))
    return render_template("invoices/index.html", invoice_form=invoice_form, settings_form=settings_form)
