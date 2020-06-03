from flask import render_template, request, current_app, send_from_directory, flash, redirect, url_for
from flask_login import login_required
from backend.invoices import bp
from models import requires_access_level
from models.user.constants import ACCESS_ADMIN, ACCESS_ORGANIZER
from constants import *
from .forms import TestInvoiceForm, InvoiceSettingsForm
from weasyprint import HTML
import os
from models.configuration import config
from ext import db


@bp.route("/", methods=[GET, POST])
@login_required
@requires_access_level(ACCESS_ADMIN, ACCESS_ORGANIZER)
def index():
    conf = config()
    invoice_form = TestInvoiceForm()
    settings_form = InvoiceSettingsForm()
    if request.method == POST:
        if invoice_form.view_invoice.name in request.form and invoice_form.validate_on_submit():
            p = invoice_form.purchase.data
            directory = os.path.join(current_app.static_folder, UPLOAD_FOLDER)
            file_name = f"invoice.{p.purchase_id}.pdf"
            path = os.path.join(directory, file_name)
            HTML(string=render_template("invoices/invoice_template.html", purchase=p, conf=conf),
                 base_url=request.base_url).write_pdf(path)
            # return render_template("invoices/invoice_template.html", purchase=p)
            return send_from_directory(directory=directory, filename=file_name, mimetype="application/pdf")
        if settings_form.save_changes.name in request.form and settings_form.validate_on_submit():
            settings_form.save()
            flash("Invoice settings saved.")
            db.session.commit()
            return redirect(url_for("invoices.index"))
    return render_template("invoices/index.html", invoice_form=invoice_form, settings_form=settings_form)
